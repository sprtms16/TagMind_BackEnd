from fastapi import FastAPI, Depends, HTTPException, status, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from dotenv import load_dotenv
import json
import uuid

# Load environment variables from .env file
load_dotenv()

from database import SessionLocal, engine, Base
import models, schemas, crud, auth

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI()

# Configure CORS middleware to allow cross-origin requests
# allow_origin_regex is used to permit all localhost ports for development
# allow_credentials is set to True to allow cookies and authorization headers
# allow_methods and allow_headers are set to "*" for broad compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",  # Allow all localhost ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Default tags for initial application setup
DEFAULT_TAGS = [
    {"name": "행복", "category": "감정"},
    {"name": "슬픔", "category": "감정"},
    {"name": "분노", "category": "감정"},
    {"name": "기쁨", "category": "감정"},
    {"name": "불안", "category": "감정"},
    {"name": "운동", "category": "활동"},
    {"name": "공부", "category": "활동"},
    {"name": "독서", "category": "활동"},
    {"name": "여행", "category": "활동"},
    {"name": "식사", "category": "일상"},
    {"name": "수면", "category": "일상"},
    {"name": "업무", "category": "일상"},
    {"name": "휴식", "category": "일상"},
    {"name": "집", "category": "장소"},
    {"name": "회사", "category": "장소"},
    {"name": "학교", "category": "장소"},
    {"name": "카페", "category": "장소"},
    {"name": "친구", "category": "관계"},
    {"name": "가족", "category": "관계"},
    {"name": "연인", "category": "관계"},
]

# Default tag packs for in-app purchase simulation
DEFAULT_TAG_PACKS = [
    {
        "name": "프리미엄 감정 팩",
        "description": "다양한 감정을 표현하는 프리미엄 태그 팩입니다.",
        "price": 1000,  # Price in cents
        "product_id": "com.tagmind.premium_emotion_pack",
        "tags": [
            {"name": "환희", "category": "감정"},
            {"name": "평온", "category": "감정"},
            {"name": "좌절", "category": "감정"},
            {"name": "희망", "category": "감정"},
        ],
    },
    {
        "name": "심화 활동 팩",
        "description": "더욱 세분화된 활동을 기록할 수 있는 태그 팩입니다.",
        "price": 1500,  # Price in cents
        "product_id": "com.tagmind.advanced_activity_pack",
        "tags": [
            {"name": "요가", "category": "활동"},
            {"name": "명상", "category": "활동"},
            {"name": "코딩", "category": "활동"},
            {"name": "등산", "category": "활동"},
        ],
    },
]


# Startup event handler to initialize default data in the database
@app.on_event("startup")
async def initialize_data():
    db = SessionLocal()
    try:
        # Initialize default tags if they don't already exist
        for tag_data in DEFAULT_TAGS:
            existing_tag = crud.get_tag_by_name(db, tag_name=tag_data["name"])
            if not existing_tag:
                crud.create_tag(
                    db=db,
                    tag=schemas.TagCreate(
                        name=tag_data["name"],
                        category=tag_data["category"],
                        is_default=True,
                    ),
                )

        # Initialize default tag packs and their associated tags if they don't already exist
        for pack_data in DEFAULT_TAG_PACKS:
            existing_pack = crud.get_tag_pack_by_product_id(
                db, product_id=pack_data["product_id"]
            )
            if not existing_pack:
                tag_pack = crud.create_tag_pack(
                    db=db,
                    tag_pack=schemas.TagPackBase(
                        name=pack_data["name"],
                        description=pack_data["description"],
                        price=pack_data["price"],
                        product_id=pack_data["product_id"],
                    ),
                )
                for tag_data in pack_data["tags"]:
                    existing_tag = crud.get_tag_by_name(db, tag_name=tag_data["name"])
                    if not existing_tag:
                        crud.create_tag(
                            db=db,
                            tag=schemas.TagCreate(
                                name=tag_data["name"],
                                category=tag_data["category"],
                                is_default=False,  # Tags in packs are not default
                                tag_pack_id=tag_pack.id,
                            ),
                        )
        db.commit()
    except Exception as e:
        # Rollback changes if any error occurs during initialization
        print(f"Error initializing data: {e}")
        db.rollback()
    finally:
        db.close()


# Root endpoint for basic API health check
@app.get("/")
async def read_root():
    return {"message": "Welcome to TagMind Backend (Revised)!"}


# --- Authentication Endpoints ---
# User registration endpoint
@app.post("/auth/signup", response_model=schemas.UserResponse)
async def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


# User login endpoint to obtain JWT token
@app.post("/auth/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not crud.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# Get current authenticated user's details
@app.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
):
    return current_user


# --- Diary CRUD Endpoints ---
# Create a new diary entry
@app.post("/diaries", response_model=schemas.DiaryResponse)
async def create_diary(
    diary_data: schemas.DiaryCreate,
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    try:
        db_diary = crud.create_diary(db=db, diary=diary_data, user_id=current_user.id)
        return db_diary
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to create diary: {e}")


# Retrieve a list of diary entries for the current user, with optional date filtering
@app.get("/diaries", response_model=List[schemas.DiaryResponse])
async def read_diaries(
    skip: int = 0,
    limit: int = 100,
    date: Optional[str] = None,  # Optional date parameter for filtering diaries by creation date
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    if date:
        # If date is provided, fetch diaries for that specific date
        return crud.get_diaries_by_date(
            db, user_id=current_user.id, date_str=date, skip=skip, limit=limit
        )
    # Otherwise, return all diaries for the user
    return crud.get_diaries(db, user_id=current_user.id, skip=skip, limit=limit)


# Retrieve a single diary entry by ID
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


# Update an existing diary entry
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
    return crud.update_diary(db=db, db_diary=db_diary, diary_update=diary)


# Delete a diary entry by ID
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


# --- Tags & Tag Store Endpoints ---
# Get all available tags for the current user (default and purchased)
@app.get("/tags", response_model=List[schemas.TagResponse])
async def get_available_tags(
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Returns all tags available to the current user (default + purchased)."""
    return crud.get_user_tags(db, user_id=current_user.id)


# Get all tag packs available for purchase in the store
@app.get("/tags/store", response_model=List[schemas.TagPackResponse])
async def get_tag_store_packs(db: Session = Depends(get_db)):
    """Returns all tag packs available for purchase in the store."""
    return crud.get_all_tag_packs(db)


# --- In-App Purchase (IAP) Endpoints ---
# Handle the purchase of a tag pack
@app.post("/iap/purchase", response_model=schemas.PurchaseResponse)
async def purchase_tag_pack(
    purchase_request: schemas.PurchaseRequest,
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Handles the purchase of a tag pack. In a real app, this would involve
    validating a receipt from the client with the App Store / Google Play.
    """
    product_id = purchase_request.product_id
    # 1. Verify the product_id is a valid tag pack
    tag_pack = crud.get_tag_pack_by_product_id(db, product_id=product_id)
    if not tag_pack:
        raise HTTPException(status_code=404, detail="Product not found.")

    # 2. Check if the user already owns this pack
    if crud.user_owns_tag_pack(db, user_id=current_user.id, tag_pack_id=tag_pack.id):
        raise HTTPException(status_code=400, detail="You already own this item.")

    # 3. Grant ownership to the user
    crud.grant_tag_pack_to_user(db, user_id=current_user.id, tag_pack_id=tag_pack.id)

    # 4. Return a success response
    return {"status": "success", "message": f"Successfully purchased {tag_pack.name}!"}


# --- Search Endpoints ---
# Search diary entries by query string, with optional date filtering
@app.get("/search", response_model=List[schemas.DiaryResponse])
async def search_diaries(
    query: str,
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    return crud.search_diaries(db, user_id=current_user.id, query=query)

