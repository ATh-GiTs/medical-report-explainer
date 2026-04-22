from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # ─── App ──────────────────────────────────────────────
    app_name: str = "Medical Report Explainer"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"

    # ─── Groq (Primary Engine) ────────────────────────────
    groq_api_key: str = ""
    groq_vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct" 
    groq_text_model: str = "llama-3.3-70b-versatile"
    groq_fast_model: str = "llama-3.1-8b-instant"
    
    # ─── Local Vector Embeddings (Keep for ChromaDB) ──────
    ollama_base_url: str = "http://localhost:11434"
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

    # ─── Logging (Add these two lines back!) ──────────────
    log_level: str = "INFO"
    log_dir: str = "./data/logs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# ─── Singleton — import this everywhere ───────────────────
settings = Settings()