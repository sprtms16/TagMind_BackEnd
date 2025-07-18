from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

from database import SessionLocal, engine, Base
import models, schemas, crud, auth, ai_service

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow all origins for development purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db(request: Request):
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def run_ai_tagging_in_background(diary_id: int, content: str, db: Session):
    """
    Background task for AI tagging.
    """
    db_diary = crud.get_diary(db, diary_id=diary_id)
    if not db_diary:
        return # Diary might have been deleted

    # v0.1: Rule-based tagging
    rule_tags = ai_service.rule_based_tagging(db_diary.content)
    for tag_name in rule_tags:
        db_tag = crud.get_tag_by_name(db, tag_name=tag_name)
        if not db_tag:
            db_tag = crud.create_tag(db=db, tag=schemas.TagCreate(name=tag_name))
        crud.add_tag_to_diary(db=db, diary_id=diary_id, tag_id=db_tag.id, source="ai_rule")

    # v0.5: External AI API (Gemini) integration
    gemini_result = await ai_service.gemini_analyze_text(db_diary.content)
    if not gemini_result.get("mock_data"): # Only process if not mock data
        # Process sentiment
        sentiment_data = gemini_result.get("sentiment")
        if sentiment_data:
            # Update or create AnalysisResult for sentiment
            pass # Implementation for AnalysisResult update/create

        # Process entities as tags
        entities = gemini_result.get("entities", [])
        for entity in entities:
            tag_name = entity.get("text")
            if tag_name:
                db_tag = crud.get_tag_by_name(db, tag_name=tag_name)
                if not db_tag:
                    db_tag = crud.create_tag(db=db, tag=schemas.TagCreate(name=tag_name))
                crud.add_tag_to_diary(db=db, diary_id=diary_id, tag_id=db_tag.id, source="ai_model")
    db.commit()


@app.get("/")
async def read_root(db: Session = Depends(get_db)):
    return {"message": "Welcome to TagMind Backend!"}

@app.post("/auth/signup", response_model=schemas.UserResponse)
async def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/auth/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not crud.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = auth.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: schemas.UserResponse = Depends(auth.get_current_user)):
    return current_user

# Diary CRUD operations
@app.post("/diaries", response_model=schemas.DiaryResponse)
async def create_diary(
    background_tasks: BackgroundTasks,
    title: str = Body(...),
    content: str = Body(...),
    tags: List[str] = Body([]),
    image_file: Optional[UploadFile] = File(None),
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    image_url = None
    if image_file:
        try:
            file_content = await image_file.read()
            file_name = f"{current_user.id}_{uuid.uuid4()}_{image_file.filename}"
            image_url = await ai_service.upload_image_to_s3(file_content, file_name, image_file.content_type)
            if not image_url:
                raise HTTPException(status_code=500, detail="Failed to upload image to S3")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")

    try:
        diary_create_data = schemas.DiaryCreate(
            title=title,
            content=content,
            image_url=image_url,
            tags=tags
        )
        db_diary = crud.create_diary(db=db, diary=diary_create_data, user_id=current_user.id)
        background_tasks.add_task(run_ai_tagging_in_background, db_diary.id, db_diary.content, db)
        return db_diary
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to create diary: {e}")

@app.get("/diaries", response_model=List[schemas.DiaryResponse])
async def read_diaries(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    diaries = crud.get_diaries(db, user_id=current_user.id, skip=skip, limit=limit)
    return diaries

@app.get("/diaries/{diary_id}", response_model=schemas.DiaryResponse)
async def read_diary(
    diary_id: int,
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db_diary = crud.get_diary(db, diary_id=diary_id)
    if db_diary is None or db_diary.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Diary not found")
    return db_diary

@app.put("/diaries/{diary_id}", response_model=schemas.DiaryResponse)
async def update_diary(
    diary_id: int,
    diary: schemas.DiaryUpdate,
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db_diary = crud.get_diary(db, diary_id=diary_id)
    if db_diary is None or db_diary.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Diary not found")
    return crud.update_diary(db=db, db_diary=db_diary, diary=diary)

@app.delete("/diaries/{diary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diary(
    diary_id: int,
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db_diary = crud.get_diary(db, diary_id=diary_id)
    if db_diary is None or db_diary.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Diary not found")
    crud.delete_diary(db=db, diary_id=diary_id)
    return

# AI Tagging and Feedback
@app.post("/ai/tagging", response_model=schemas.DiaryResponse)
async def ai_tagging(
    diary_id: int,
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db_diary = crud.get_diary(db, diary_id=diary_id)
    if db_diary is None or db_diary.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Diary not found")

    # v0.1: Rule-based tagging
    rule_tags = ai_service.rule_based_tagging(db_diary.content)
    for tag_name in rule_tags:
        db_tag = crud.get_tag_by_name(db, tag_name=tag_name)
        if not db_tag:
            db_tag = crud.create_tag(db=db, tag=schemas.TagCreate(name=tag_name))
        crud.add_tag_to_diary(db=db, diary_id=diary_id, tag_id=db_tag.id, source="ai_rule")

    # v0.5: External AI API (Gemini) integration
    gemini_result = await ai_service.gemini_analyze_text(db_diary.content)
    if not gemini_result.get("mock_data"): # Only process if not mock data
        # Process sentiment
        sentiment_data = gemini_result.get("sentiment")
        if sentiment_data:
            # Update or create AnalysisResult for sentiment
            pass # Implementation for AnalysisResult update/create

        # Process entities as tags
        entities = gemini_result.get("entities", [])
        for entity in entities:
            tag_name = entity.get("text")
            if tag_name:
                db_tag = crud.get_tag_by_name(db, tag_name=tag_name)
                if not db_tag:
                    db_tag = crud.create_tag(db=db, tag=schemas.TagCreate(name=tag_name))
                crud.add_tag_to_diary(db=db, diary_id=diary_id, tag_id=db_tag.id, source="ai_model")

    db.refresh(db_diary) # Refresh to get updated tags
    return db_diary

@app.post("/ai/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def ai_feedback(
    diary_id: int,
    tag_id: int,
    action: str, # "add" or "remove"
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db_diary = crud.get_diary(db, diary_id=diary_id)
    if db_diary is None or db_diary.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Diary not found")

    if action == "add":
        crud.add_tag_to_diary(db=db, diary_id=diary_id, tag_id=tag_id, source="user_feedback")
    elif action == "remove":
        crud.remove_tag_from_diary(db=db, diary_id=diary_id, tag_id=tag_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'add' or 'remove'")
    return

# Tag operations
@app.post("/diaries/{diary_id}/tags", response_model=schemas.DiaryResponse)
async def add_tag_to_diary(
    diary_id: int,
    tag_create: schemas.TagCreate,
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db_diary = crud.get_diary(db, diary_id=diary_id)
    if db_diary is None or db_diary.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Diary not found")

    db_tag = crud.get_tag_by_name(db, tag_name=tag_create.name)
    if not db_tag:
        db_tag = crud.create_tag(db=db, tag=tag_create)

    crud.add_tag_to_diary(db=db, diary_id=diary_id, tag_id=db_tag.id)
    return db_diary

@app.delete("/diaries/{diary_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_diary(
    diary_id: int,
    tag_id: int,
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db_diary = crud.get_diary(db, diary_id=diary_id)
    if db_diary is None or db_diary.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Diary not found")

    crud.remove_tag_from_diary(db=db, diary_id=diary_id)
    return

# Analytics API
@app.get("/analytics/mood-over-time", response_model=List[schemas.MoodOverTimeResponse])
async def get_mood_over_time(
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    # Placeholder for actual mood analysis logic
    # This would involve querying AnalysisResult table and aggregating sentiment scores over time.
    return [
        {"date": "2024-01-01", "mood_score": 0.7},
        {"date": "2024-01-02", "mood_score": 0.8},
        {"date": "2024-01-03", "mood_score": 0.6},
    ]

@app.get("/analytics/tag-correlation", response_model=List[schemas.TagCorrelationResponse])
async def get_tag_correlation(
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    # Placeholder for actual tag correlation logic
    # This would involve analyzing co-occurrence of tags in diaries.
    return [
        {"tag1": "운동", "tag2": "행복", "correlation_score": 0.75},
        {"tag1": "공부", "tag2": "성장", "correlation_score": 0.82},
    ]

# Payment API (Placeholder)
@app.post("/payment/process", response_model=schemas.PaymentResponse)
async def process_payment(
    payment_request: schemas.PaymentRequest,
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
):
    # Placeholder for actual payment gateway integration (e.g., Stripe, Toss Payments)
    # In a real scenario, you would interact with a payment gateway API.
    print(f"Processing payment for user {current_user.email}: {payment_request.amount} {payment_request.currency}")
    return {"transaction_id": "mock_txn_12345", "status": "success"}

# Search operations
@app.get("/search", response_model=List[schemas.DiaryResponse])
async def search_diaries(
    query: str,
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    # This is a basic search. For full-text search, consider using PostgreSQL's FTS features
    # or a dedicated search engine like Elasticsearch.
    search_results = db.query(models.Diary).join(models.DiaryTag).join(models.Tag).filter(
        models.Diary.user_id == current_user.id,
        (models.Diary.content.ilike(f"%{query}%") | models.Tag.name.ilike(f"%{query}%"))
    ).distinct().all()
    return search_results

