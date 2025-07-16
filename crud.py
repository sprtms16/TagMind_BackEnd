from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, password_hash=hashed_password, nickname=user.nickname)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_diary(db: Session, diary: schemas.DiaryCreate, user_id: int):
    db_diary = models.Diary(**diary.dict(), user_id=user_id)
    db.add(db_diary)
    db.commit()
    db.refresh(db_diary)
    return db_diary

def get_diary(db: Session, diary_id: int):
    return db.query(models.Diary).filter(models.Diary.id == diary_id).first()

def get_diaries(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Diary).filter(models.Diary.user_id == user_id).offset(skip).limit(limit).all()

def update_diary(db: Session, db_diary: models.Diary, diary: schemas.DiaryUpdate):
    for key, value in diary.dict(exclude_unset=True).items():
        setattr(db_diary, key, value)
    db.add(db_diary)
    db.commit()
    db.refresh(db_diary)
    return db_diary

def delete_diary(db: Session, diary_id: int):
    db_diary = db.query(models.Diary).filter(models.Diary.id == diary_id).first()
    if db_diary:
        db.delete(db_diary)
        db.commit()
    return db_diary
