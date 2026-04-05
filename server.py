from datetime import datetime, timedelta, timezone
import os

from fastapi import FastAPI, HTTPException, Depends
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


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    gutenberg_id = Column(String(50), unique=True, nullable=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    genre = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    file_path = Column(String(1000), nullable=True)
    favorites = relationship("Favorite", back_populates="book", cascade="all, delete-orphan")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_user_book_favorite"),)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user = relationship("User", back_populates="favorites")
    book = relationship("Book", back_populates="favorites")


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BookOut(BaseModel):
    id: int
    gutenberg_id: str | None = None
    title: str
    author: str
    genre: str
    description: str | None = None
    file_path: str | None = None

    class Config:
        from_attributes = True


class FavoriteBookOut(BaseModel):
    id: int
    book: BookOut

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


Base.metadata.create_all(bind=engine)

app = FastAPI(title="AziBax Quick API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_BOOKS = [
    {
        "gutenberg_id": "1661",
        "title": "Sherlock Holmes",
        "author": "Arthur Conan Doyle",
        "genre": "detective",
        "description": "Классический детектив о Шерлоке Холмсе."
    },
    {
        "gutenberg_id": "2680",
        "title": "Meditations",
        "author": "Marcus Aurelius",
        "genre": "self_development",
        "description": "Философия стоицизма и личной дисциплины."
    },
    {
        "gutenberg_id": "2542",
        "title": "A Doll's House",
        "author": "Henrik Ibsen",
        "genre": "drama",
        "description": "Одна из самых известных драм мировой литературы."
    },
    {
        "gutenberg_id": "66048",
        "title": "The Interpretation of Dreams",
        "author": "Sigmund Freud",
        "genre": "psychology",
        "description": "Классический труд по психоанализу."
    }
]


@app.get("/")
def root():
    return {"name": "AziBax Quick API", "status": "ok", "docs": "/docs"}


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
def list_books(db: Session = Depends(get_db)):
    books = db.query(Book).order_by(Book.id.desc()).all()
    if books:
        return books

    for item in DEMO_BOOKS:
        db.add(Book(**item))
    db.commit()

    return db.query(Book).order_by(Book.id.desc()).all()


@app.get("/books/search", response_model=list[BookOut])
def search_books(q: str, db: Session = Depends(get_db)):
    q = q.strip().lower()
    books = db.query(Book).all()
    return [b for b in books if q in b.title.lower() or q in b.author.lower()]


@app.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.get("/favorites", response_model=list[FavoriteBookOut])
def list_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Favorite).filter(Favorite.user_id == current_user.id).all()


@app.post("/favorites/{book_id}")
def add_favorite(book_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.book_id == book_id
    ).first()

    if existing:
        return {"message": "Already in favorites"}

    fav = Favorite(user_id=current_user.id, book_id=book_id)
    db.add(fav)
    db.commit()
    return {"message": "Added to favorites"}


@app.delete("/favorites/{book_id}")
def remove_favorite(book_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fav = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.book_id == book_id
    ).first()

    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")

    db.delete(fav)
    db.commit()
    return {"message": "Removed from favorites"}
