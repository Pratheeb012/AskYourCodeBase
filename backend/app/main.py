from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core import storage
from app.api import repos, chat, auth

# Ensure all data directories exist on startup
storage._ensure_dirs()

app = FastAPI(
    title="Ask Your Codebase API",
    description="AI-powered RAG system using Groq + FAISS — no database required",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api")
app.include_router(repos.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/api/health")
def health_check():
    repo_count = len(storage.list_repos())
    return {
        "status": "ok",
        "message": "Ask Your Codebase API is running",
        "model": settings.GROQ_MODEL,
        "repos_indexed": repo_count,
    }
