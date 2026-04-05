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

@router.get("/books")
def get_books():
    return books
