from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from sqlalchemy.sql import func
from datetime import datetime
import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# --- User ---
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email, password_hash=hashed_password, nickname=user.nickname
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- Diary ---
def create_diary(db: Session, diary: schemas.DiaryCreate, user_id: int):
    db_diary = models.Diary(
        title=diary.title,
        content=diary.content,
        image_url=diary.image_url,
        user_id=user_id,
    )
    db.add(db_diary)
    db.flush()

    for tag_id in diary.tags:
        db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
        if db_tag:
            db_diary.tags.append(db_tag)

    db.commit()
    db.refresh(db_diary)
    return db_diary


def get_diary(db: Session, diary_id: int):
    return (
        db.query(models.Diary)
        .options(joinedload(models.Diary.tags))
        .filter(models.Diary.id == diary_id)
        .first()
    )


def get_diaries(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Diary)
        .filter(models.Diary.user_id == user_id)
        .order_by(models.Diary.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_diaries_by_date(
    db: Session, user_id: int, date_str: str, skip: int = 0, limit: int = 100
):
    from datetime import datetime

    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    return (
        db.query(models.Diary)
        .filter(
            models.Diary.user_id == user_id,
            func.date(models.Diary.created_at) == target_date,
        )
        .order_by(models.Diary.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_diary(
    db: Session, db_diary: models.Diary, diary_update: schemas.DiaryUpdate
):
    if diary_update.title is not None:
        db_diary.title = diary_update.title
    if diary_update.content is not None:
        db_diary.content = diary_update.content
    if diary_update.image_url is not None:
        db_diary.image_url = diary_update.image_url

    # Clear existing tags and add new ones
    if diary_update.tags is not None:
        db_diary.tags.clear()
        db.flush()

        for tag_id in diary_update.tags:
            db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
            if db_tag:
                db_diary.tags.append(db_tag)

    db.commit()
    db.refresh(db_diary)
    return db_diary


def delete_diary(db: Session, diary_id: int):
    db_diary = db.query(models.Diary).filter(models.Diary.id == diary_id).first()
    if db_diary:
        db.delete(db_diary)
        db.commit()


# --- Tag & Tag Pack ---
def get_tag_by_name(db: Session, tag_name: str):
    return db.query(models.Tag).filter(models.Tag.name == tag_name).first()


def create_tag(db: Session, tag: schemas.TagCreate):
    db_tag = models.Tag(
        name=tag.name,
        category=tag.category,
        is_default=tag.is_default,
        tag_pack_id=tag.tag_pack_id,
    )
    db.add(db_tag)
    db.flush()
    db.refresh(db_tag)
    return db_tag


def create_tag_pack(db: Session, tag_pack: schemas.TagPackBase):
    db_tag_pack = models.TagPack(
        name=tag_pack.name,
        description=tag_pack.description,
        price=tag_pack.price,
        product_id=tag_pack.product_id,
    )
    db.add(db_tag_pack)
    db.flush()
    db.refresh(db_tag_pack)
    return db_tag_pack


def get_user_tags(db: Session, user_id: int):
    """Gets all default tags and tags from packs the user has purchased."""
    # Get tags from purchased packs
    purchased_tags = (
        db.query(models.Tag)
        .join(models.TagPack)
        .join(models.UserTagPack)
        .filter(models.UserTagPack.user_id == user_id)
        .all()
    )
    # Get default tags (those not in any pack)
    default_tags = db.query(models.Tag).filter(models.Tag.is_default == True).all()
    return list(set(default_tags + purchased_tags))


def get_all_tag_packs(db: Session):
    return db.query(models.TagPack).options(joinedload(models.TagPack.tags)).all()


def get_tag_pack_by_product_id(db: Session, product_id: str):
    return (
        db.query(models.TagPack).filter(models.TagPack.product_id == product_id).first()
    )


def user_owns_tag_pack(db: Session, user_id: int, tag_pack_id: int):
    return (
        db.query(models.UserTagPack)
        .filter(
            and_(
                models.UserTagPack.user_id == user_id,
                models.UserTagPack.tag_pack_id == tag_pack_id,
            )
        )
        .first()
        is not None
    )


def grant_tag_pack_to_user(db: Session, user_id: int, tag_pack_id: int):
    db_user_tag_pack = models.UserTagPack(user_id=user_id, tag_pack_id=tag_pack_id)
    db.add(db_user_tag_pack)
    db.commit()


# --- Search ---
def search_diaries(db: Session, user_id: int, query: str):
    return (
        db.query(models.Diary)
        .outerjoin(models.Diary.tags) # Use outerjoin to include diaries without tags
        .filter(
            models.Diary.user_id == user_id,
            (
                models.Diary.title.ilike(f"%{query}%")
                | models.Diary.content.ilike(f"%{query}%")
                | models.Tag.name.ilike(f"%{query}%")
            ),
        )
        .distinct()
        .all()
    )
