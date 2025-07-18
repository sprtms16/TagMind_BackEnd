from sqlalchemy.orm import Session
import models, schemas
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
    db_diary = models.Diary(title=diary.title, content=diary.content, image_url=diary.image_url, user_id=user_id)
    db.add(db_diary)
    db.flush() # Flush to get the diary ID before committing

    for tag_name in diary.tags:
        db_tag = get_tag_by_name(db, tag_name)
        if not db_tag:
            db_tag = create_tag(db, schemas.TagCreate(name=tag_name))
        add_tag_to_diary(db, db_diary.id, db_tag.id)

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

def get_tag_by_name(db: Session, tag_name: str):
    return db.query(models.Tag).filter(models.Tag.name == tag_name).first()

def create_tag(db: Session, tag: schemas.TagCreate):
    db_tag = models.Tag(name=tag.name)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def add_tag_to_diary(db: Session, diary_id: int, tag_id: int, source: str = "manual"):
    db_diary_tag = models.DiaryTag(diary_id=diary_id, tag_id=tag_id, source=source)
    db.add(db_diary_tag)
    db.commit()
    db.refresh(db_diary_tag)
    return db_diary_tag

def remove_tag_from_diary(db: Session, diary_id: int, tag_id: int):
    db_diary_tag = db.query(models.DiaryTag).filter(
        models.DiaryTag.diary_id == diary_id,
        models.DiaryTag.tag_id == tag_id
    ).first()
    if db_diary_tag:
        db.delete(db_diary_tag)
        db.commit()
    return db_diary_tag

def get_analysis_result_by_diary_id(db: Session, diary_id: int):
    return db.query(models.AnalysisResult).filter(models.AnalysisResult.diary_id == diary_id).first()

def create_analysis_result(db: Session, diary_id: int, sentiment: dict, entities: list):
    db_analysis_result = models.AnalysisResult(
        diary_id=diary_id,
        sentiment=sentiment,
        entities=entities
    )
    db.add(db_analysis_result)
    db.commit()
    db.refresh(db_analysis_result)
    return db_analysis_result

def update_analysis_result(db: Session, analysis_result_id: int, sentiment: dict, entities: list):
    db_analysis_result = db.query(models.AnalysisResult).filter(models.AnalysisResult.id == analysis_result_id).first()
    if db_analysis_result:
        db_analysis_result.sentiment = sentiment
        db_analysis_result.entities = entities
        db.commit()
        db.refresh(db_analysis_result)
    return db_analysis_result

def upsert_analysis_result(db: Session, diary_id: int, sentiment: dict, entities: list):
    existing_result = get_analysis_result_by_diary_id(db, diary_id)
    if existing_result:
        return update_analysis_result(db, existing_result.id, sentiment, entities)
    else:
        return create_analysis_result(db, diary_id, sentiment, entities)