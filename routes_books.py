from typing import Optional
from fastapi import APIRouter, Query

router = APIRouter(prefix="/books", tags=["books"])

# Пока оставляем демо-тексты.
# Позже сюда подключим реальные txt/epub файлы.
DEMO_TEXT = """
Глава 1

Это первая версия встроенного reader для AziBax.

Теперь книга открывается прямо внутри сайта,
а читатель не уходит на другие платформы.

Следующим этапом мы подключим реальные книги
из твоей собственной библиотеки.
""".strip()


@router.get("")
def list_books(
    q: Optional[str] = Query(default="classic literature"),
    language: Optional[str] = Query(default=None),
    limit: int = Query(default=18, ge=1, le=100),
):
    """
    Пока не ломаем текущую выдачу.
    Если у тебя уже был рабочий список книг, этот маршрут можно оставить как есть.
    """
    import requests

    params = {"q": q, "limit": limit}
    if language:
        params["language"] = language

    response = requests.get("https://openlibrary.org/search.json", params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    books = []
    for doc in data.get("docs", []):
        key = doc.get("key", "")
        title = doc.get("title") or "Без названия"
        author = doc["author_name"][0] if doc.get("author_name") else "Неизвестный автор"
        language_value = doc["language"][0] if doc.get("language") else "unknown"
        cover_id = doc.get("cover_i")

        books.append({
            "id": key,
            "title": title,
            "author": author,
            "genre": None,
            "description": f"{title} — {author}",
            "language": language_value,
            "cover": f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None,
            "openlibrary_url": f"https://openlibrary.org{key}" if key else None,
        })

    return books


@router.get("/search")
def search_books(
    q: str = Query(..., min_length=1),
    language: Optional[str] = Query(default=None),
    limit: int = Query(default=18, ge=1, le=100),
):
    import requests

    params = {"q": q, "limit": limit}
    if language:
        params["language"] = language

    response = requests.get("https://openlibrary.org/search.json", params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    books = []
    for doc in data.get("docs", []):
        key = doc.get("key", "")
        title = doc.get("title") or "Без названия"
        author = doc["author_name"][0] if doc.get("author_name") else "Неизвестный автор"
        language_value = doc["language"][0] if doc.get("language") else "unknown"
        cover_id = doc.get("cover_i")

        books.append({
            "id": key,
            "title": title,
            "author": author,
            "genre": None,
            "description": f"{title} — {author}",
            "language": language_value,
            "cover": f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None,
            "openlibrary_url": f"https://openlibrary.org{key}" if key else None,
        })

    return books


@router.get("/read")
def read_book(book_id: str = Query(...)):
    return {
        "book_id": book_id,
        "text": DEMO_TEXT
    }
