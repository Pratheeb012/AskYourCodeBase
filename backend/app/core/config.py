from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Groq AI
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Embedding
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Storage
    FAISS_INDEX_PATH: str = "./data/faiss_indexes"
    UPLOAD_DIR: str = "./data/uploads"
    DATA_DIR: str = "./data"

    # Limits
    MAX_REPO_SIZE_MB: int = 500

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # GitHub (optional)
    GITHUB_TOKEN: Optional[str] = None

    # JWT Auth
    SECRET_KEY: str = "change-me-to-a-random-secret-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()
