from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Table,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# Base class for declarative models
Base = declarative_base()

# Association table for many-to-many relationship between Diary and Tag
# This table stores the relationships between diaries and tags.
diary_tags_association = Table(
    "diary_tags",
    Base.metadata,
    Column("diary_id", Integer, ForeignKey("diaries.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class User(Base):
    """Represents a user in the application."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)  # Hashed password for security
    nickname = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Timestamp of user creation
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # Timestamp of last update

    # Relationships to other models
    diaries = relationship("Diary", back_populates="owner")
    user_tag_packs = relationship("UserTagPack", back_populates="user")


class Diary(Base):
    """Represents a diary entry."""
    __tablename__ = "diaries"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=True)  # Content can be derived from tags or user input
    image_url = Column(String, nullable=True)  # URL for an associated image
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Timestamp of diary creation
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )  # Timestamp of last update, defaults to creation time
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Foreign key to User model

    # Relationships to other models
    owner = relationship("User", back_populates="diaries")
    tags = relationship(
        "Tag", secondary=diary_tags_association, back_populates="diaries"
    )  # Many-to-many relationship with Tag model


class Tag(Base):
    """Represents a tag that can be associated with diary entries."""
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=False)  # e.g., "Emotion", "Activity", "Place"
    is_default = Column(
        Boolean, default=False, nullable=False
    )  # True for default tags, False for purchasable tags
    tag_pack_id = Column(
        Integer, ForeignKey("tag_packs.id"), nullable=True
    )  # Null for default tags, links to TagPack for purchasable tags

    # Relationships to other models
    tag_pack = relationship("TagPack", back_populates="tags")
    diaries = relationship(
        "Diary", secondary=diary_tags_association, back_populates="tags"
    )


class TagPack(Base):
    """Represents a collection of tags available for purchase."""
    __tablename__ = "tag_packs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Integer, nullable=False)  # Price in cents or smallest currency unit
    product_id = Column(
        String, unique=True, nullable=False
    )  # Product ID from App Store/Google Play for IAP
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Timestamp of tag pack creation

    # Relationships to other models
    tags = relationship("Tag", back_populates="tag_pack")
    user_tag_packs = relationship("UserTagPack", back_populates="tag_pack")


class UserTagPack(Base):
    """Represents a user's ownership of a tag pack."""
    __tablename__ = "user_tag_packs"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    tag_pack_id = Column(Integer, ForeignKey("tag_packs.id"), primary_key=True)
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())  # Timestamp of purchase

    # Relationships to other models
    user = relationship("User", back_populates="user_tag_packs")
    tag_pack = relationship("TagPack", back_populates="user_tag_packs")
