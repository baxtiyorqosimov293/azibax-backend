from datetime import datetime, timedelta, timezone
import os
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./azibax.db")
SECRET_KEY = os.getenv("SECRET_KEY", "change_me_please_123456789")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

OPENLIBRARY_SEARCH = "https://openlibrary.org/search.json"
COVERS_BASE = "https://covers.openlibrary.org/b/id"

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")


class FavoriteBook(Base):
    __tablename__ = "favorite_books"
    __table_args__ = (UniqueConstraint("user_id", "book_key", name="uq_user_book_key"),)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_key = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    author = Column(String(255), nullable=True)
    genre = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    cover_url = Column(String(1000), nullable=True)
    openlibrary_url = Column(String(1000), nullable=True)

    user = relationship("User", back_populates="favorites")


User.favorites = relationship("FavoriteBook", back_populates="user", cascade="all, delete-orphan")


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BookOut(BaseModel):
    id: str
    title: str
    author: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    cover: Optional[str] = None
    openlibrary_url: Optional[str] = None


class FavoriteOut(BaseModel):
    id: int
    book_key: str
    title: str
    author: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    openlibrary_url: Optional[str] = None

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(sub: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": sub, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def map_language(code: Optional[str]) -> str:
    mapping = {
        "eng": "English",
        "rus": "Русский",
        "uzb": "O'zbek",
    }
    return mapping.get(code or "", code or "Unknown")


def build_cover_url(cover_id: Optional[int]) -> Optional[str]:
    if not cover_id:
        return None
    return f"{COVERS_BASE}/{cover_id}-L.jpg"


def normalize_doc(doc: dict) -> dict:
    author = None
    if doc.get("author_name"):
        author = doc["author_name"][0]

    subjects = doc.get("subject") or []
    genre = subjects[0] if subjects else None

    language = None
    if doc.get("language"):
        language = map_language(doc["language"][0])

    key = doc.get("key", "")
    openlibrary_url = f"https://openlibrary.org{key}" if key else None

    return {
        "id": key or str(doc.get("cover_i") or doc.get("edition_key", [""])[0]),
        "title": doc.get("title") or "Untitled",
        "author": author,
        "genre": genre,
        "description": f"{doc.get('title', 'Untitled')} — {author or 'Unknown author'}",
        "language": language,
        "cover": build_cover_url(doc.get("cover_i")),
        "openlibrary_url": openlibrary_url,
    }


def search_openlibrary(q: str, language: Optional[str] = None, limit: int = 20):
    params = {"q": q, "limit": limit}
    if language:
        params["language"] = language

    response = requests.get(OPENLIBRARY_SEARCH, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    docs = data.get("docs", [])
    return [normalize_doc(doc) for doc in docs]


Base.metadata.create_all(bind=engine)

app = FastAPI(title="AziBax API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "AziBax API", "status": "ok", "docs": "/docs"}


@app.post("/auth/register")
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "full_name": user.full_name}


@app.post("/auth/login", response_model=TokenOut)
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}


@app.get("/books", response_model=list[BookOut])
def get_books(
    q: str = Query("popular fiction", description="Search query"),
    language: Optional[str] = Query(None, description="eng, rus, uzb"),
    limit: int = Query(20, ge=1, le=50),
):
    return search_openlibrary(q=q, language=language, limit=limit)


@app.get("/books/search", response_model=list[BookOut])
def search_books(
    q: str,
    language: Optional[str] = Query(None, description="eng, rus, uzb"),
    limit: int = Query(20, ge=1, le=50),
):
    return search_openlibrary(q=q, language=language, limit=limit)


@app.get("/books/{book_id}")
def get_book(book_id: str):
    # Упрощенно: фронт и так получает всё из /books; для страницы можно передавать данные из списка
    raise HTTPException(status_code=404, detail="Use /books or /books/search for catalog results")


@app.get("/favorites", response_model=list[FavoriteOut])
def list_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(FavoriteBook).filter(FavoriteBook.user_id == current_user.id).all()


@app.post("/favorites/{book_id}")
def add_favorite(
    book_id: str,
    title: str,
    author: Optional[str] = None,
    genre: Optional[str] = None,
    description: Optional[str] = None,
    cover_url: Optional[str] = None,
    openlibrary_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(FavoriteBook).filter(
        FavoriteBook.user_id == current_user.id,
        FavoriteBook.book_key == book_id
    ).first()

    if existing:
        return {"message": "Already in favorites"}

    fav = FavoriteBook(
        user_id=current_user.id,
        book_key=book_id,
        title=title,
        author=author,
        genre=genre,
        description=description,
        cover_url=cover_url,
        openlibrary_url=openlibrary_url,
    )
    db.add(fav)
    db.commit()
    return {"message": "Added to favorites"}


@app.delete("/favorites/{book_id}")
def remove_favorite(book_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fav = db.query(FavoriteBook).filter(
        FavoriteBook.user_id == current_user.id,
        FavoriteBook.book_key == book_id
    ).first()

    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")

    db.delete(fav)
    db.commit()
    return {"message": "Removed from favorites"}
