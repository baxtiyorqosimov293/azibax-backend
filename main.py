from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import Base, engine
from .config import LIBRARY_PATH
from .routes_auth import router as auth_router
from .routes_books import router as books_router
from .routes_favorites import router as favorites_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AziBax Kitob API",
    version="1.0.0",
    description="MVP backend for a legal book platform.",
)

app.include_router(auth_router)
app.include_router(books_router)
app.include_router(favorites_router)

@app.get("/")
def root():
    return {"name": "AziBax Kitob API", "status": "ok", "docs": "/docs"}

if LIBRARY_PATH.exists():
    app.mount("/library", StaticFiles(directory=str(LIBRARY_PATH)), name="library")
