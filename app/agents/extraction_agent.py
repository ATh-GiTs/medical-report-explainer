import uuid
from app.services.groq_service import groq_service
from app.services.vector_store import vector_store
from app.utils.pdf_parser import extract_text_from_pdf, chunk_text
from app.models.schemas import ExtractedReportData, ReportType, MedicalParameter
from app.core.logger import logger

# ─── System prompt for medical extraction ─────────────────
EXTRACTION_SYSTEM_PROMPT = """You are a medical document analysis expert. 
Your job is to analyze medical reports and extract key information accurately.
Always be precise, factual, and never make up medical information.
If something is unclear, say so rather than guessing."""

class ExtractionAgent:
    """
    Agentic Document Extraction — intelligently parses medical reports,
    classifies them, extracts structured data, and indexes them for RAG.
    """

    def process_report(self, file_path: str, filename: str) -> ExtractedReportData:
        report_id = str(uuid.uuid4())[:8]  
        logger.info(f"Processing report: {filename} (ID: {report_id})")

        # ─── Step 1: Extract raw text from PDF ────────────
        raw_text = extract_text_from_pdf(file_path)
        if not raw_text.strip():
            raise ValueError("Could not extract text from this PDF. Is it a scanned image?")

        # ─── Step 2: Classify report type ─────────────────
        report_type = self._classify_report(raw_text)
        logger.info(f"Report classified as: {report_type}")

        # ─── Step 3: Extract structured parameters ─────────
        parameters = self._extract_parameters(raw_text, report_type)

        # ─── Step 4: Extract metadata ──────────────────────
        metadata = self._extract_metadata(raw_text)

        # ─── Step 5: Chunk and store in vector DB ──────────
        chunks = chunk_text(raw_text, chunk_size=400, overlap=50)
        vector_store.add_chunks(report_id, chunks)

        # ─── Step 6: Build structured output ──────────────
        report_data = ExtractedReportData(
            report_id=report_id,
            patient_name=metadata.get("patient_name"),
            report_type=report_type,
            report_date=metadata.get("report_date"),
            doctor_name=metadata.get("doctor_name"),
            hospital_name=metadata.get("hospital_name"),
            parameters=parameters,
            raw_text=raw_text,
            confidence_score=0.85 if parameters else 0.6,
        )

        logger.info(f"Extraction complete — {len(parameters)} parameters found")
        return report_data

    def _classify_report(self, text: str) -> ReportType:
        prompt = f"""Look at this medical document text and classify it.
        
Text (first 500 chars): {text[:500]}

Reply with ONLY one of these exact words:
- blood_test
- radiology  
- prescription
- discharge_summary
- unknown

Your answer:"""

        try:
            response = groq_service.generate(prompt, EXTRACTION_SYSTEM_PROMPT, model_type="fast")
            response = response.strip().lower()
            for report_type in ReportType:
                if report_type.value in response:
                    return report_type
            return ReportType.UNKNOWN
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return ReportType.UNKNOWN

    def _extract_parameters(self, text: str, report_type: ReportType) -> list[MedicalParameter]:
        if report_type not in [ReportType.BLOOD_TEST]:
            return []

        prompt = f"""Extract medical test parameters from this blood test report.
        
CRITICAL INSTRUCTION: You MUST output the data EXACTLY in the format below. 
Do NOT use markdown tables. Do NOT use bullet points. Do NOT add extra text.
Start EVERY single extracted line with the exact word "PARAM:".

Format:
PARAM: name | value | unit | normal_range | abnormal(yes/no)

Report text:
{text[:3000]}"""

        try:
            response = groq_service.generate(prompt, EXTRACTION_SYSTEM_PROMPT, model_type="report")
            # Debugging print to check AI output in terminal
            print(f"\n--- RAW GROQ OUTPUT ---\n{response}\n-----------------------\n")
            return self._parse_parameters(response)
        except Exception as e:
            logger.error(f"Parameter extraction failed: {e}")
            return []

    def _parse_parameters(self, response: str) -> list[MedicalParameter]:
        parameters = []
        for line in response.split("\n"):
            # Clean rogue markdown formatting
            clean_line = line.replace("**", "").replace("*", "").strip()
            
            if "PARAM:" in clean_line.upper():
                try:
                    idx = clean_line.upper().find("PARAM:")
                    content = clean_line[idx + 6:]
                    parts = content.split("|")
                    
                    if len(parts) >= 2:
                        param = MedicalParameter(
                            name=parts[0].strip().title(),
                            value=parts[1].strip(),
                            unit=parts[2].strip() if len(parts) > 2 else None,
                            normal_range=parts[3].strip() if len(parts) > 3 else None,
                            is_abnormal=parts[4].strip().lower() == "yes" if len(parts) > 4 else None,
                        )
                        parameters.append(param)
                except Exception as e:
                    logger.warning(f"Skipped a messy line during parsing: {line}")
                    continue
        return parameters

    def _extract_metadata(self, text: str) -> dict:
        prompt = f"""Extract these details from the medical report if present:
- Patient name
- Report date
- Doctor name  
- Hospital name

Report text:
{text[:1000]}

Reply in this exact format:
patient_name: <value or unknown>
report_date: <value or unknown>
doctor_name: <value or unknown>
hospital_name: <value or unknown>"""

        try:
            response = groq_service.generate(prompt, EXTRACTION_SYSTEM_PROMPT, model_type="fast")
            metadata = {}
            for line in response.split("\n"):
                if ":" in line:
                    key, _, value = line.partition(":")
                    value = value.strip()
                    if value and value.lower() != "unknown":
                        metadata[key.strip()] = value
            return metadata
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {}

# ─── Singleton ────────────────────────────────────────────
extraction_agent = ExtractionAgent()