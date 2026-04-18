from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ─── App ──────────────────────────────────────────────
    app_name: str = "Medical Report Explainer"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"

    # ─── Ollama ───────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "alibayram/medgemma"
    ollama_fallback_model: str = "llama3.2:3b"
    ollama_embed_model: str = "nomic-embed-text"

    # ─── ChromaDB ─────────────────────────────────────────
    chroma_persist_dir: str = "./data/vectorstore"
    chroma_collection_name: str = "medical_reports"

    # ─── File Upload ──────────────────────────────────────
    max_file_size_mb: int = 10
    upload_dir: str = "./data/uploads"

    # ─── Translation ──────────────────────────────────────
    default_language: str = "en"
    supported_languages: List[str] = ["en", "hi", "mr", "ta", "bn", "te", "gu"]

    # ─── Logging ──────────────────────────────────────────
    log_level: str = "INFO"
    log_dir: str = "./data/logs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# ─── Singleton — import this everywhere ───────────────────
settings = Settings()
