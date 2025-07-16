from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nickname = Column(String)
    provider = Column(String, default="email")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    diaries = relationship("Diary", back_populates="owner")

class Diary(Base):
    __tablename__ = "diaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    image_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="diaries")
    diary_tags = relationship("DiaryTag", back_populates="diary")
    analysis_results = relationship("AnalysisResult", back_populates="diary", uselist=False)

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    diary_tags = relationship("DiaryTag", back_populates="tag")

class DiaryTag(Base):
    __tablename__ = "diary_tags"

    diary_id = Column(Integer, ForeignKey("diaries.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    source = Column(String, default="manual") # 'manual', 'ai_rule', 'ai_model'

    diary = relationship("Diary", back_populates="diary_tags")
    tag = relationship("Tag", back_populates="diary_tags")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    diary_id = Column(Integer, ForeignKey("diaries.id", ondelete="CASCADE"), unique=True)
    sentiment = Column(JSON) # Example: {"label": "positive", "score": 0.98}
    entities = Column(JSON)  # Example: [{"text": "김민준", "type": "PERSON"}, {"text": "사무실", "type": "LOCATION"}]
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())

    diary = relationship("Diary", back_populates="analysis_results")
