from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .models import Favorite, Book
from .schemas import FavoriteOut
from .auth import get_current_user

router = APIRouter(prefix="/favorites", tags=["favorites"])

@router.get("", response_model=list[FavoriteOut])
def list_favorites(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Favorite).filter(Favorite.user_id == current_user.id).all()

@router.post("/{book_id}")
def add_favorite(book_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    existing = db.query(Favorite).filter(Favorite.user_id == current_user.id, Favorite.book_id == book_id).first()
    if existing:
        return {"message": "Already in favorites"}
    fav = Favorite(user_id=current_user.id, book_id=book_id)
    db.add(fav)
    db.commit()
    return {"message": "Added to favorites"}

@router.delete("/{book_id}")
def remove_favorite(book_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    fav = db.query(Favorite).filter(Favorite.user_id == current_user.id, Favorite.book_id == book_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()
    return {"message": "Removed from favorites"}
