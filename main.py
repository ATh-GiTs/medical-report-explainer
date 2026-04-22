from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings
from app.core.logger import logger


# ─── Create FastAPI app ───────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered Medical Report Explainer with multilingual support",
    docs_url="/docs",       # Swagger UI at /docs
    redoc_url="/redoc",     # ReDoc UI at /redoc
)

# ─── CORS (allows Streamlit to talk to FastAPI) ───────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Include all routes ───────────────────────────────────
app.include_router(router, prefix="/api/v1")


# ─── Startup event ────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Medical Report Explainer API...")
    logger.info(f"⚡ Using Groq Text model: {settings.groq_text_model}")
    logger.info(f"👁️ Using Groq Vision model: {settings.groq_vision_model}")


# ─── Run directly ─────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
