import os
import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.agents.extraction_agent import extraction_agent
from app.agents.query_agent import query_agent
from app.models.schemas import (
    ReportUploadResponse,
    QueryRequest,
    QueryResponse,
    HealthResponse,
)
from app.services.ollama_service import ollama_service
from app.services.translation_service import translation_service
from app.core.config import settings
from app.core.logger import logger

router = APIRouter()


# ─── Health Check ─────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the API and Ollama are running correctly."""
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        ollama_connected=ollama_service.is_connected(),
    )


# ─── Upload Report ────────────────────────────────────────
@router.post("/report/upload", response_model=ReportUploadResponse)
async def upload_report(file: UploadFile = File(...)):
    """
    Upload a medical report PDF.
    Extracts text, classifies it, indexes it in ChromaDB.
    """
    # ─── Validate file type ───────────────────────────────
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # ─── Validate file size ───────────────────────────────
    file_bytes = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB."
        )

    # ─── Save file to disk ────────────────────────────────
    os.makedirs(settings.upload_dir, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # ─── Process with extraction agent ────────────────────
    try:
        logger.info(f"Processing uploaded file: {file.filename}")
        report_data = extraction_agent.process_report(file_path, file.filename)

        return ReportUploadResponse(
            report_id=report_data.report_id,
            filename=file.filename,
            report_type=report_data.report_type,
            parameters_found=len(report_data.parameters),
            message=f"Report processed successfully! Found {len(report_data.parameters)} medical parameters.",
            extracted_at=report_data.extracted_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Report processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process report. Please try again.")


# ─── Ask Question ─────────────────────────────────────────
@router.post("/report/query", response_model=QueryResponse)
async def query_report(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # This offloads the heavy AI generation to a separate thread
        # so the main thread stays awake for health checks
        response = await asyncio.to_thread(query_agent.answer, request)
        return response
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail="Could not generate answer.")

@router.get("/health", response_model=HealthResponse)
def health_check():  # Removed 'async' here too
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        ollama_connected=ollama_service.is_connected(),
    )

# ─── Get Supported Languages ──────────────────────────────
@router.get("/languages")
async def get_languages():
    """Return all supported languages for translation."""
    return translation_service.get_supported_languages()
