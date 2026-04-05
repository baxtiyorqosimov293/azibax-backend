from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from .database import get_db
from .models import Book
from .schemas import BookOut

router = APIRouter(prefix="/books", tags=["books"])

@router.get("", response_model=list[BookOut])
def list_books(genre: Optional[str] = None, limit: int = Query(20, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    query = db.query(Book)
    if genre:
        query = query.filter(Book.genre.ilike(genre))
    return query.order_by(Book.id.desc()).offset(offset).limit(limit).all()

@router.get("/search", response_model=list[BookOut])
def search_books(q: str, limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    q_like = f"%{q}%"
    return db.query(Book).filter(or_(Book.title.ilike(q_like), Book.author.ilike(q_like))).order_by(Book.id.desc()).limit(limit).all()

@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
