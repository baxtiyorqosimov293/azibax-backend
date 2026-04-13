from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/books", tags=["books"])

BASE_DIR = Path(__file__).resolve().parent
LIBRARY_DIR = BASE_DIR / "library" / "books"

BOOKS = [
    {
        "id": "gosudar",
        "title": "Государь",
        "author": "Никколо Макиавелли",
        "description": "Классический трактат о власти, управлении и политическом искусстве.",
        "language": "Русский",
        "genre": "История",
        "cover": None,
        "file_name": "gosudar.txt",
    },
    {
        "id": "sherlock",
        "title": "Шерлок Холмс",
        "author": "Артур Конан Дойл",
        "description": "Знаменитые расследования, наблюдательность и искусство дедукции.",
        "language": "Русский",
        "genre": "Детектив",
        "cover": None,
        "file_name": "sherlock.txt",
    },
    {
        "id": "razmyshleniya",
        "title": "Размышления",
        "author": "Марк Аврелий",
        "description": "Записи о внутренней дисциплине, спокойствии и ясности ума.",
        "language": "Русский",
        "genre": "Саморазвитие",
        "cover": None,
        "file_name": "razmyshleniya.txt",
    },
]


def _public_book(book: dict) -> dict:
    return {
        "id": book["id"],
        "title": book["title"],
        "author": book["author"],
        "description": book["description"],
        "language": book["language"],
        "genre": book["genre"],
        "cover": book["cover"],
    }


def _filter_books(
    q: Optional[str] = None,
    language: Optional[str] = None,
    genre: Optional[str] = None,
) -> list[dict]:
    results = BOOKS

    if language:
        lang_lower = language.strip().lower()
        results = [
            book for book in results
            if (book.get("language") or "").strip().lower() == lang_lower
        ]

    if genre:
        genre_lower = genre.strip().lower()
        results = [
            book for book in results
            if (book.get("genre") or "").strip().lower() == genre_lower
        ]

    if q:
        q_lower = q.strip().lower()
        results = [
            book for book in results
            if q_lower in (book.get("title") or "").lower()
            or q_lower in (book.get("author") or "").lower()
            or q_lower in (book.get("description") or "").lower()
        ]

    return results


@router.get("")
def list_books(
    q: Optional[str] = Query(default=None),
    language: Optional[str] = Query(default=None),
    genre: Optional[str] = Query(default=None),
    limit: int = Query(default=18, ge=1, le=100),
):
    books = _filter_books(q=q, language=language, genre=genre)
    return [_public_book(book) for book in books[:limit]]


@router.get("/search")
def search_books(
    q: str = Query(..., min_length=1),
    language: Optional[str] = Query(default=None),
    genre: Optional[str] = Query(default=None),
    limit: int = Query(default=18, ge=1, le=100),
):
    books = _filter_books(q=q, language=language, genre=genre)
    return [_public_book(book) for book in books[:limit]]


@router.get("/read")
def read_book(book_id: str = Query(...)):
    book = next((b for b in BOOKS if b["id"] == book_id), None)

    if not book:
      raise HTTPException(status_code=404, detail="Книга не найдена")

    file_name = book.get("file_name")
    if not file_name:
      raise HTTPException(status_code=404, detail="У книги нет файла")

    file_path = LIBRARY_DIR / file_name

    if not file_path.exists():
      raise HTTPException(status_code=404, detail="Файл книги не найден")

    text = file_path.read_text(encoding="utf-8")

    return {
        "book_id": book["id"],
        "title": book["title"],
        "author": book["author"],
        "text": text
    }


@router.get("/{book_id}")
def get_book(book_id: str):
    book = next((b for b in BOOKS if b["id"] == book_id), None)

    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    return _public_book(book)
