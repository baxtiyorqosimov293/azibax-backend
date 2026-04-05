from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class BookOut(BaseModel):
    id: int
    gutenberg_id: Optional[str] = None
    title: str
    author: str
    genre: str
    description: Optional[str] = None
    language: Optional[str] = None
    year: Optional[str] = None
    cover_url: Optional[str] = None
    file_path: Optional[str] = None
    class Config:
        from_attributes = True

class FavoriteOut(BaseModel):
    id: int
    book: BookOut
    class Config:
        from_attributes = True
