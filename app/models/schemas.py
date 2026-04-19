from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────
class ReportType(str, Enum):
    BLOOD_TEST = "blood_test"
    RADIOLOGY = "radiology"
    PRESCRIPTION = "prescription"
    DISCHARGE_SUMMARY = "discharge_summary"
    UNKNOWN = "unknown"


class SeverityLevel(str, Enum):
    NORMAL = "normal"
    LOW = "low"
    HIGH = "high"
    CRITICAL = "critical"


class SupportedLanguage(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    MARATHI = "mr"
    TAMIL = "ta"
    BENGALI = "bn"
    TELUGU = "te"
    GUJARATI = "gu"


# ─── Medical Parameter ────────────────────────────────────
class MedicalParameter(BaseModel):
    name: str
    value: str
    unit: Optional[str] = None
    normal_range: Optional[str] = None
    is_abnormal: Optional[bool] = None
    severity: Optional[SeverityLevel] = None


# ─── Report Models ────────────────────────────────────────
class ExtractedReportData(BaseModel):
    report_id: str
    patient_name: Optional[str] = None
    report_type: ReportType = ReportType.UNKNOWN
    report_date: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    parameters: List[MedicalParameter] = []
    raw_text: str
    extracted_at: datetime = Field(default_factory=datetime.now)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ReportUploadResponse(BaseModel):
    report_id: str
    filename: str
    report_type: ReportType
    parameters_found: int
    message: str
    extracted_at: datetime


# ─── Query Models ─────────────────────────────────────────
class QueryRequest(BaseModel):
    report_id: str
    question: str
    target_language: SupportedLanguage = SupportedLanguage.ENGLISH
    include_voice: bool = False


class QueryResponse(BaseModel):
    report_id: str
    question: str
    answer_english: str
    answer_translated: Optional[str] = None
    target_language: str
    source_chunks: List[str] = []
    voice_file_path: Optional[str] = None
    response_time_ms: float


# ─── Translation Models ───────────────────────────────────
class TranslationRequest(BaseModel):
    text: str
    target_language: SupportedLanguage
    include_voice: bool = False


class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    target_language: str
    voice_file_path: Optional[str] = None


# ─── Health Check ─────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    ollama_connected: bool
    timestamp: datetime = Field(default_factory=datetime.now)

# ─── Prescription Models ──────────────────────────────────
class PrescriptionItem(BaseModel):
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    purpose: Optional[str] = None
    instructions: Optional[str] = None
    warnings: Optional[str] = None


class PrescriptionExplanation(BaseModel):
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None
    date: Optional[str] = None
    medicines: List[PrescriptionItem] = []
    general_instructions: Optional[str] = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    raw_text: Optional[str] = None


class PrescriptionUploadResponse(BaseModel):
    filename: str
    medicines_found: int
    explanation: PrescriptionExplanation
    message: str