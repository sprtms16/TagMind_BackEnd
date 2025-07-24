import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Diary, Tag, TagPack, UserTagPack
from crud import (
    get_tag_by_name,
    create_tag,
    create_diary,
    update_diary,
    get_diary,
    get_all_tag_packs,
    create_tag_pack,
    get_tag_pack_by_product_id,
    user_owns_tag_pack,
    grant_tag_pack_to_user,
    search_diaries,
    get_diaries_by_date,
)
from schemas import TagCreate, DiaryCreate, DiaryUpdate, TagPackBase
from datetime import datetime, timedelta

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
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
    tag_in = TagCreate(name=tag_name, category="감정")
    tag = create_tag(db, tag_in)
    assert tag.name == tag_name
    assert tag.id is not None

    retrieved_tag = get_tag_by_name(db, tag_name)
    assert retrieved_tag.id == tag.id


def test_get_tag_by_name(db):
    tag_name = "existing_tag"
    create_tag(db, TagCreate(name=tag_name, category="활동"))
    tag = get_tag_by_name(db, tag_name)
    assert tag.name == tag_name

    non_existent_tag = get_tag_by_name(db, "non_existent_tag")
    assert non_existent_tag is None


def test_add_tag_to_diary(db):
    # Create a user
    user = User(
        email="test@example.com", password_hash="hashed_password", nickname="testuser"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create a tag
    tag_name = "diary_tag"
    tag = create_tag(db, TagCreate(name=tag_name, category="일상"))

    # Create a diary with the tag
    diary_in = DiaryCreate(title="Test Diary", content="This is a test diary.", tags=[tag.id])
    diary = create_diary(db, diary_in, user.id)

    # Verify relationship
    retrieved_diary = get_diary(db, diary.id)
    assert len(retrieved_diary.tags) == 1
    assert retrieved_diary.tags[0].name == tag_name


def test_remove_tag_from_diary(db):
    # Create a user
    user = User(
        email="test2@example.com", password_hash="hashed_password", nickname="testuser2"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create a tag
    tag_name = "removable_tag"
    tag = create_tag(db, TagCreate(name=tag_name, category="장소"))

    # Create a diary with the tag
    diary_in = DiaryCreate(title="Another Diary", content="Content for another diary.", tags=[tag.id])
    diary = create_diary(db, diary_in, user.id)

    # Verify relationship
    retrieved_diary = get_diary(db, diary.id)
    assert len(retrieved_diary.tags) == 1

    # Remove tag from diary by updating it with an empty tag list
    diary_update_in = DiaryUpdate(tags=[])
    updated_diary = update_diary(db, retrieved_diary, diary_update_in)

    # Verify removal
    assert len(updated_diary.tags) == 0


def test_create_tag_pack(db):
    tag_pack_in = TagPackBase(
        name="Premium Pack",
        description="A premium tag pack",
        price=1000,
        product_id="premium_pack_1",
    )
    tag_pack = create_tag_pack(db, tag_pack_in)
    assert tag_pack.name == "Premium Pack"
    assert tag_pack.product_id == "premium_pack_1"


def test_get_all_tag_packs(db):
    create_tag_pack(
        db,
        TagPackBase(
            name="Pack1", description="Desc1", price=100, product_id="p1"
        ),
    )
    create_tag_pack(
        db,
        TagPackBase(
            name="Pack2", description="Desc2", price=200, product_id="p2"
        ),
    )
    packs = get_all_tag_packs(db)
    assert len(packs) == 2


def test_get_tag_pack_by_product_id(db):
    create_tag_pack(
        db,
        TagPackBase(
            name="Pack3", description="Desc3", price=300, product_id="p3"
        ),
    )
    pack = get_tag_pack_by_product_id(db, "p3")
    assert pack.name == "Pack3"


def test_user_owns_tag_pack(db):
    user = User(email="owner@example.com", password_hash="hashed", nickname="owner")
    db.add(user)
    db.commit()
    db.refresh(user)

    tag_pack = create_tag_pack(
        db,
        TagPackBase(
            name="Owned Pack", description="Desc", price=10, product_id="owned"
        ),
    )
    grant_tag_pack_to_user(db, user.id, tag_pack.id)
    assert user_owns_tag_pack(db, user.id, tag_pack.id) is True
    assert user_owns_tag_pack(db, user.id, tag_pack.id + 1) is False


def test_grant_tag_pack_to_user(db):
    user = User(email="grant@example.com", password_hash="hashed", nickname="grant")
    db.add(user)
    db.commit()
    db.refresh(user)

    tag_pack = create_tag_pack(
        db,
        TagPackBase(
            name="Grant Pack", description="Desc", price=10, product_id="grant"
        ),
    )
    grant_tag_pack_to_user(db, user.id, tag_pack.id)
    # Check if the entry exists in the UserTagPack table
    user_tag_pack_entry = (
        db.query(UserTagPack)
        .filter_by(user_id=user.id, tag_pack_id=tag_pack.id)
        .first()
    )
    assert user_tag_pack_entry is not None


def test_search_diaries_by_title(db):
    user = User(email="search1@example.com", password_hash="hashed", nickname="search1")
    db.add(user)
    db.commit()
    db.refresh(user)

    create_diary(db, DiaryCreate(title="My Happy Day", content="Content"), user.id)
    create_diary(db, DiaryCreate(title="Sad Thoughts", content="Content"), user.id)

    results = search_diaries(db, user.id, "Happy")
    assert len(results) == 1
    assert results[0].title == "My Happy Day"


def test_search_diaries_by_content(db):
    user = User(email="search2@example.com", password_hash="hashed", nickname="search2")
    db.add(user)
    db.commit()
    db.refresh(user)

    create_diary(db, DiaryCreate(title="Title", content="This is about joy"), user.id)
    create_diary(db, DiaryCreate(title="Title", content="This is about sorrow"), user.id)

    results = search_diaries(db, user.id, "joy")
    assert len(results) == 1
    assert results[0].content == "This is about joy"


def test_search_diaries_by_tag_name(db):
    user = User(email="search3@example.com", password_hash="hashed", nickname="search3")
    db.add(user)
    db.commit()
    db.refresh(user)

    tag1 = create_tag(db, TagCreate(name="여행", category="활동"))
    tag2 = create_tag(db, TagCreate(name="공부", category="활동"))

    create_diary(db, DiaryCreate(title="Travel", content="", tags=[tag1.id]), user.id)
    create_diary(db, DiaryCreate(title="Study", content="", tags=[tag2.id]), user.id)

    results = search_diaries(db, user.id, "여행")
    assert len(results) == 1
    assert results[0].title == "Travel"


def test_get_diaries_by_date(db):
    user = User(email="date_test@example.com", password_hash="hashed", nickname="date_test")
    db.add(user)
    db.commit()
    db.refresh(user)

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # Create a diary for today
    diary_today = Diary(title="Today's Diary", content="", user_id=user.id, created_at=datetime.combine(today, datetime.min.time()))
    db.add(diary_today)

    # Create a diary for yesterday
    diary_yesterday = Diary(title="Yesterday's Diary", content="", user_id=user.id, created_at=datetime.combine(yesterday, datetime.min.time()))
    db.add(diary_yesterday)
    db.commit()

    results_today = get_diaries_by_date(db, user.id, today.strftime("%Y-%m-%d"))
    assert len(results_today) == 1
    assert results_today[0].title == "Today's Diary"

    results_yesterday = get_diaries_by_date(db, user.id, yesterday.strftime("%Y-%m-%d"))
    assert len(results_yesterday) == 1
    assert results_yesterday[0].title == "Yesterday's Diary"

    results_tomorrow = get_diaries_by_date(db, user.id, (today + timedelta(days=1)).strftime("%Y-%m-%d"))
    assert len(results_tomorrow) == 0
