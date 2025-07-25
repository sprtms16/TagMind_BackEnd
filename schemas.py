from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date


# --- User Schemas ---
# Schema for creating a new user
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nickname: Optional[str] = None


# Schema for user response (excluding sensitive information like password hash)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    nickname: Optional[str] = None
    created_at: datetime

    class Config:
        # Enable ORM mode for Pydantic to read data from SQLAlchemy models
        from_attributes = True


# Schema for JWT token response
class Token(BaseModel):
    access_token: str
    token_type: str


# Schema for JWT token data (payload)
class TokenData(BaseModel):
    email: Optional[str] = None


# --- Tag Schemas ---
# Schema for creating a new tag
class TagCreate(BaseModel):
    name: str
    category: str
    is_default: bool = False
    tag_pack_id: Optional[int] = None


# Schema for tag response
class TagResponse(BaseModel):
    id: int
    name: str
    category: str
    is_default: bool
    tag_pack_id: Optional[int]

    class Config:
        from_attributes = True


# --- Tag Pack Schemas ---
# Base schema for a tag pack (used for creation/request bodies)
class TagPackBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: int
    product_id: str


# Schema for tag pack response (including ID, creation date, and associated tags)
class TagPackResponse(TagPackBase):
    id: int
    created_at: datetime
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True


# --- Diary Schemas ---
# Schema for creating a new diary entry
class DiaryCreate(BaseModel):
    title: str
    content: Optional[str] = None  # Content can be derived from tags or user input
    image_url: Optional[str] = None
    tags: List[int] = []  # List of tag IDs to associate with the diary


# Schema for updating an existing diary entry
class DiaryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[List[int]] = None  # List of tag IDs to update


# Schema for diary entry response
class DiaryResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []  # List of Tag objects associated with the diary

    class Config:
        from_attributes = True


# --- In-App Purchase Schemas ---
# Schema for purchase request body
class PurchaseRequest(BaseModel):
    product_id: str


# Schema for purchase response
class PurchaseResponse(BaseModel):
    status: str
    message: str


# --- Calendar Schemas ---
class CalendarDaySummary(BaseModel):
    date: date
    count: int

    class Config:
        from_attributes = True