import os
import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.agents.extraction_agent import extraction_agent
from app.agents.query_agent import query_agent
from app.agents.prescription_agent import prescription_agent
from app.models.schemas import (
    ReportUploadResponse,
    QueryRequest,
    QueryResponse,
    HealthResponse,
    PrescriptionUploadResponse,
)
from app.services.groq_service import groq_service
from app.services.translation_service import translation_service
from app.core.config import settings
from app.core.logger import logger

router = APIRouter()


# ─── Health Check ─────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the API and Groq are running correctly."""
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        # We keep the variable name 'ollama_connected' so your frontend and schemas don't break, 
        # but it is now actively checking your Groq API connection!
        ollama_connected=groq_service.is_connected(),
    )


# ─── Upload Report ────────────────────────────────────────
@router.post("/report/upload", response_model=ReportUploadResponse)
async def upload_report(file: UploadFile = File(...)):
    """
    Upload a medical report PDF.
    Extracts text, classifies it, indexes it in ChromaDB.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB."
        )

    os.makedirs(settings.upload_dir, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

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
        response = await asyncio.to_thread(query_agent.answer, request)
        return response
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail="Could not generate answer.")


# ─── Get Supported Languages ──────────────────────────────
@router.get("/languages")
async def get_languages():
    """Return all supported languages for translation."""
    return translation_service.get_supported_languages()


# ─── Upload Prescription ──────────────────────────────────
@router.post("/prescription/upload", response_model=PrescriptionUploadResponse)
async def upload_prescription(file: UploadFile = File(...)):
    """
    Upload a prescription as PDF or image (JPG/PNG).
    Reads medicines, dosages and enriches with purpose/warnings.
    """
    allowed = [".pdf", ".jpg", ".jpeg", ".png"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: PDF, JPG, PNG"
        )

    file_bytes = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum {settings.max_file_size_mb}MB allowed."
        )

    os.makedirs(settings.upload_dir, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    file_type = "pdf" if ext == ".pdf" else "image"

    try:
        explanation = prescription_agent.process_prescription(
            file_path, file.filename, file_type
        )
        return PrescriptionUploadResponse(
            filename=file.filename,
            medicines_found=len(explanation.medicines),
            explanation=explanation,
            message=f"Found {len(explanation.medicines)} medicine(s) in prescription."
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Prescription processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to read prescription.")