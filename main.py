from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional

from .database import SessionLocal, engine, Base
from . import models, schemas, crud, auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get DB session
def get_db(request: Request):
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
    diary: schemas.DiaryCreate = Depends(),
    current_user: schemas.UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    # Placeholder for image upload to S3. For now, image_url is directly from input.
    # In a real scenario, you would upload the file to S3 and get the URL.
    return crud.create_diary(db=db, diary=diary, user_id=current_user.id)

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
