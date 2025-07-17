import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Diary, Tag, DiaryTag
from crud import get_tag_by_name, create_tag, add_tag_to_diary, remove_tag_from_diary
from schemas import TagCreate

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db")
def session_fixture():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_create_tag(db):
    tag_name = "test_tag"
    tag_in = TagCreate(name=tag_name)
    tag = create_tag(db, tag_in)
    assert tag.name == tag_name
    assert tag.id is not None

    retrieved_tag = get_tag_by_name(db, tag_name)
    assert retrieved_tag.id == tag.id

def test_get_tag_by_name(db):
    tag_name = "existing_tag"
    create_tag(db, TagCreate(name=tag_name))
    tag = get_tag_by_name(db, tag_name)
    assert tag.name == tag_name

    non_existent_tag = get_tag_by_name(db, "non_existent_tag")
    assert non_existent_tag is None

def test_add_tag_to_diary(db):
    # Create a user
    user = User(email="test@example.com", password_hash="hashed_password", nickname="testuser")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create a diary
    diary = Diary(title="Test Diary", content="This is a test diary.", user_id=user.id)
    db.add(diary)
    db.commit()
    db.refresh(diary)

    # Create a tag
    tag_name = "diary_tag"
    tag = create_tag(db, TagCreate(name=tag_name))

    # Add tag to diary
    diary_tag = add_tag_to_diary(db, diary.id, tag.id, source="manual")
    assert diary_tag.diary_id == diary.id
    assert diary_tag.tag_id == tag.id
    assert diary_tag.source == "manual"

    # Verify relationship
    db.refresh(diary)
    assert len(diary.diary_tags) == 1
    assert diary.diary_tags[0].tag.name == tag_name

def test_remove_tag_from_diary(db):
    # Create a user
    user = User(email="test2@example.com", password_hash="hashed_password", nickname="testuser2")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create a diary
    diary = Diary(title="Another Diary", content="Content for another diary.", user_id=user.id)
    db.add(diary)
    db.commit()
    db.refresh(diary)

    # Create a tag
    tag_name = "removable_tag"
    tag = create_tag(db, TagCreate(name=tag_name))

    # Add tag to diary
    add_tag_to_diary(db, diary.id, tag.id, source="manual")
    db.refresh(diary)
    assert len(diary.diary_tags) == 1

    # Remove tag from diary
    removed_diary_tag = remove_tag_from_diary(db, diary.id, tag.id)
    assert removed_diary_tag.diary_id == diary.id
    assert removed_diary_tag.tag_id == tag.id

    # Verify removal
    db.refresh(diary)
    assert len(diary.diary_tags) == 0
