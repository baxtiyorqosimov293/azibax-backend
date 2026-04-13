from fastapi import APIRouter

router = APIRouter()

books = [
    {
        "id": 1,
        "title": "Sherlock Holmes",
        "author": "Arthur Conan Doyle",
        "cover": "https://covers.openlibrary.org/b/id/8225261-L.jpg",
        "description": "Classic detective stories."
    },
    {
        "id": 2,
        "title": "Meditations",
        "author": "Marcus Aurelius",
        "cover": "https://covers.openlibrary.org/b/id/8231996-L.jpg",
        "description": "Stoic philosophy of Marcus Aurelius."
    },
    {
        "id": 3,
        "title": "A Doll’s House",
        "author": "Henrik Ibsen",
        "cover": "https://covers.openlibrary.org/b/id/8225631-L.jpg",
        "description": "Famous drama play."
    },
    {
        "id": 4,
        "title": "The Interpretation of Dreams",
        "author": "Sigmund Freud",
        "cover": "https://covers.openlibrary.org/b/id/8235116-L.jpg",
        "description": "Psychoanalysis classic."
    }
]
@router.get("/{book_id}")
def get_book(book_id: str):
    return {
        "id": book_id,
        "title": f"Книга #{book_id}",
        "author": "AziBax Library",
        "description": "Демонстрационная книга"
    }
@router.get("/{book_id}/read")
def read_book(book_id: str):
    sample_texts = {
        "1": "Глава 1\n\nЭто первая книга в библиотеке AziBax. Здесь будет настоящий текст книги.",
        "2": "Глава 1\n\nВторая книга открыта внутри сайта. Пользователь остаётся в AziBax.",
    }

    text = sample_texts.get(
        str(book_id),
        "Это демонстрационный режим reader. Следующим этапом сюда подключаются реальные тексты книг из файлов .txt или .epub."
    )

    return {"book_id": book_id, "text": text}
