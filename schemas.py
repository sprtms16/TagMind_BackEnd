from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nickname: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    nickname: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class DiaryCreate(BaseModel):
    content: str
    image_url: Optional[str] = None

class DiaryUpdate(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None

class DiaryResponse(BaseModel):
    id: int
    user_id: int
    content: str
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    diary_tags: List[DiaryTagResponse] = []

    class Config:
        orm_mode = True

class TagCreate(BaseModel):
    name: str

class TagResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class DiaryTagResponse(BaseModel):
    tag_id: int
    source: str
    tag: TagResponse

    class Config:
        orm_mode = True