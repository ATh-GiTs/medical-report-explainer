import base64
import re
import httpx
from PIL import Image, ImageEnhance
import io
import pytesseract
from app.services.ollama_service import ollama_service
from app.models.schemas import PrescriptionExplanation, PrescriptionItem
from app.utils.pdf_parser import extract_text_from_pdf
from app.core.config import settings
from app.core.logger import logger

# --- WINDOWS TESSERACT PATH ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ─── Medicine Database ────────────────────────────────────
MEDICINE_DB = {
    "paracetamol": {"use": "Fever and mild to moderate pain relief", "warnings": "Do not exceed 4g per day. Avoid alcohol.", "common_brands": "Calpol, Dolo 650, Crocin"},
    "amoxicillin": {"use": "Bacterial infections (throat, ear, chest, urinary)", "warnings": "Complete the full course even if feeling better.", "common_brands": "Mox, Novamox, Amoxil"},
    "metformin": {"use": "Type 2 Diabetes — controls blood sugar levels", "warnings": "Take with meals to avoid stomach upset. Avoid alcohol.", "common_brands": "Glycomet, Glucophage"},
    "atorvastatin": {"use": "Lowers cholesterol and reduces heart disease risk", "warnings": "Take at night. Report any muscle pain.", "common_brands": "Atorva, Lipitor"},
    "omeprazole": {"use": "Acidity, heartburn, stomach ulcers", "warnings": "Take 30 minutes before meals.", "common_brands": "Omez, Prilosec"},
    "azithromycin": {"use": "Bacterial infections", "warnings": "Take on empty stomach. Complete full course.", "common_brands": "Azee, Zithromax"},
    "cetirizine": {"use": "Allergies, hay fever, runny nose", "warnings": "May cause drowsiness. Avoid driving.", "common_brands": "Cetriz, Zyrtec"},
    "pantoprazole": {"use": "Acidity, GERD, stomach ulcers", "warnings": "Take before breakfast on empty stomach.", "common_brands": "Pan, Pantocid"},
    "ibuprofen": {"use": "Pain, fever, inflammation", "warnings": "Always take with food.", "common_brands": "Brufen, Combiflam"},
    "amlodipine": {"use": "High blood pressure and chest pain", "warnings": "Do not stop suddenly. May cause ankle swelling.", "common_brands": "Amlip, Norvasc"},
    "losartan": {"use": "High blood pressure and kidney protection", "warnings": "Do not use during pregnancy.", "common_brands": "Losar, Cozaar"},
    "aspirin": {"use": "Pain relief, blood thinning", "warnings": "Avoid on empty stomach.", "common_brands": "Ecosprin, Disprin"},
    "glimepiride": {"use": "Type 2 Diabetes — lowers blood sugar", "warnings": "Take with first meal of day.", "common_brands": "Glimer, Amaryl"},
    "levothyroxine": {"use": "Thyroid hormone replacement", "warnings": "Take on empty stomach 30 mins before breakfast.", "common_brands": "Thyronorm, Eltroxin"},
    "montelukast": {"use": "Asthma and allergic rhinitis prevention", "warnings": "Take in the evening.", "common_brands": "Montair, Singulair"},
}

# ─── System Prompt ────────────────────────────────────────
PRESCRIPTION_SYSTEM_PROMPT = """You are a medical prescription reading expert.
Your job is to carefully read doctor prescriptions and extract medicine information.
Rules:
1. Read every medicine name carefully — fix any obvious typos from the OCR scanner (e.g., 'Am1odip1ne' -> 'Amlodipine').
2. Make your best guess at unclear words using medical knowledge.
3. Be precise and never make up medicines that are not there.
4. If a field is truly unreadable, output 'Unknown'.
5. Always follow the EXACT block output format requested.
6. CRITICAL SAFETY RULE: Be highly critical of dosages. OCR scanners often confuse '1.0' with '10' or '5' with 'S'. Ensure the dosage makes logical medical sense for the extracted medicine."""

class PrescriptionAgent:
    """
    Reads prescriptions from PDF or image files.
    Uses Tesseract OCR with a custom Medical Dictionary for images, 
    text extraction for PDFs, and LLM for structuring.
    """

    def __init__(self):
        self.text_model = settings.ollama_model

    def process_prescription(self, file_path: str, filename: str, file_type: str) -> PrescriptionExplanation:
        logger.info(f"Processing prescription: {filename} (type: {file_type})")
        if file_type == "pdf":
            return self._process_pdf_prescription(file_path)
        else:
            return self._process_image_prescription(file_path)

    def _process_pdf_prescription(self, file_path: str) -> PrescriptionExplanation:
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            raise ValueError("Could not extract text from this PDF.")
        return self._extract_from_text(text)

    # ─────────────────────────────────────────────────────
    # HYBRID OCR IMAGE HANDLER WITH CUSTOM DICTIONARY
    # ─────────────────────────────────────────────────────
    def _process_image_prescription(self, file_path: str) -> PrescriptionExplanation:
        logger.info("Processing image with Tesseract OCR...")

        try:
            with Image.open(file_path) as img:
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")

                # --- PRE-PROCESSING FOR BETTER OCR ---
                img = img.convert('L') # Grayscale
                img = ImageEnhance.Contrast(img).enhance(2.0) # High Contrast
                img = ImageEnhance.Sharpness(img).enhance(1.5) # Crisp Edges
                
                # --- RUN TESSERACT WITH CUSTOM DICTIONARY ---
                # PSM 6: Assume a single uniform block of text.
                # user-words: Point to your custom medical dictionary file.
                custom_config = r'--psm 6 --user-words C:\Users\91876\Desktop\Medical_Report_Explainer\medical_words.txt'
                
                ocr_text = pytesseract.image_to_string(img, config=custom_config)

                print("\n" + "="*40)
                print("TESSERACT RAW OCR TEXT (TUNED):")
                print(ocr_text.strip())
                print("="*40 + "\n")

                if len(ocr_text.strip()) < 5:
                    return self._fallback_response("OCR could not read the handwriting clearly enough.")

                logger.info("Sending tuned OCR text to LLM for structuring...")
                return self._extract_from_text(ocr_text)

        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract is not installed on the OS.")
            return self._fallback_response("Tesseract software is missing. Please install it on Windows.")
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return self._fallback_response(str(e))

    # ─────────────────────────────────────────────────────
    # Text Extraction (Used by both PDF and OCR)
    # ─────────────────────────────────────────────────────
    def _extract_from_text(self, text: str) -> PrescriptionExplanation:
        prompt = f"""Read this raw OCR text from a prescription and extract all medicines. Fix any obvious spelling mistakes caused by the scanner.

Prescription text:
{text[:3000]}

You must output ONLY a strict list of information using this exact format:

DOCTOR: [Doctor Name or Unknown]
PATIENT: [Patient Name or Unknown]
DATE: [Date or Unknown]
GENERAL: [Any general notes or Unknown]
---
MEDICINE: [Medicine Name]
DOSAGE: [Amount or Unknown]
FREQUENCY: [How often or Unknown]
DURATION: [How long or Unknown]
INSTRUCTIONS: [Special notes or Unknown]

Separate each medicine block with '---'. Do not include conversational text."""

        response = ollama_service.generate(prompt, PRESCRIPTION_SYSTEM_PROMPT, model_type="report")
        
        print("\n" + "="*40)
        print("LLM STRUCTURED OUTPUT:")
        print(response)
        print("="*40 + "\n")
        
        return self._parse_prescription_response(response)

    def _parse_prescription_response(self, response: str) -> PrescriptionExplanation:
        doctor_name, patient_name, date, general_instructions = None, None, None, None
        medicines = []
        blocks = response.split("---")

        for block in blocks:
            med_name = dosage = frequency = duration = instructions = None
            is_med_block = False

            for line in block.strip().split("\n"):
                line = line.strip()
                if not line: continue
                upper = line.upper()

                if upper.startswith("DOCTOR:"): doctor_name = line.split(":", 1)[1].strip()
                elif upper.startswith("PATIENT:"): patient_name = line.split(":", 1)[1].strip()
                elif upper.startswith("DATE:"): date = line.split(":", 1)[1].strip()
                elif upper.startswith("GENERAL:"): general_instructions = line.split(":", 1)[1].strip()
                elif upper.startswith("MEDICINE:"):
                    is_med_block = True
                    med_name = line.split(":", 1)[1].strip()
                elif upper.startswith("DOSAGE:"): dosage = line.split(":", 1)[1].strip()
                elif upper.startswith("FREQUENCY:"): frequency = line.split(":", 1)[1].strip()
                elif upper.startswith("DURATION:"): duration = line.split(":", 1)[1].strip()
                elif upper.startswith("INSTRUCTIONS:"): instructions = line.split(":", 1)[1].strip()

            invalid = ["unknown", "n/a", "", "[medicine name]"]
            if is_med_block and med_name and med_name.lower() not in invalid:
                medicine = PrescriptionItem(
                    medicine_name=med_name,
                    dosage=dosage if dosage and dosage.lower() not in invalid else None,
                    frequency=frequency if frequency and frequency.lower() not in invalid else None,
                    duration=duration if duration and duration.lower() not in invalid else None,
                    instructions=instructions if instructions and instructions.lower() not in invalid else None,
                )
                medicines.append(self._enrich_with_db(medicine))

        return PrescriptionExplanation(
            doctor_name=doctor_name, patient_name=patient_name, date=date,
            medicines=medicines, general_instructions=general_instructions,
            confidence_score=0.9 if medicines else 0.2, raw_text=response
        )

    def _enrich_with_db(self, medicine: PrescriptionItem) -> PrescriptionItem:
        name_lower = medicine.medicine_name.lower()
        for key, info in MEDICINE_DB.items():
            if key in name_lower or name_lower in key:
                medicine.purpose = info["use"]
                medicine.warnings = f"{info['warnings']} | Common brands: {info['common_brands']}"
                break
        return medicine

    def _fallback_response(self, reason: str) -> PrescriptionExplanation:
        return PrescriptionExplanation(confidence_score=0.0, general_instructions="Could not read prescription.", raw_text=reason)

prescription_agent = PrescriptionAgent()