import base64
from PIL import Image, ImageEnhance
import io
from app.services.groq_service import groq_service
from app.models.schemas import PrescriptionExplanation, PrescriptionItem
from app.utils.pdf_parser import extract_text_from_pdf
from app.core.logger import logger

# Medical Database for cross-referencing extracted medicines
MEDICINE_DB = {
    "paracetamol":   {"use": "Fever and mild to moderate pain relief",            "warnings": "Do not exceed 4g per day. Avoid alcohol.",              "common_brands": "Calpol, Dolo 650, Crocin"},
    "amoxicillin":   {"use": "Bacterial infections (throat, ear, chest, urinary)","warnings": "Complete the full course even if feeling better.",      "common_brands": "Mox, Novamox, Amoxil"},
    "metformin":     {"use": "Type 2 Diabetes — controls blood sugar levels",     "warnings": "Take with meals to avoid stomach upset. Avoid alcohol.","common_brands": "Glycomet, Glucophage"},
    "atorvastatin":  {"use": "Lowers cholesterol and reduces heart disease risk", "warnings": "Take at night. Report any muscle pain.",                "common_brands": "Atorva, Lipitor"},
    "omeprazole":    {"use": "Acidity, heartburn, stomach ulcers",                "warnings": "Take 30 minutes before meals.",                         "common_brands": "Omez, Prilosec"},
    "azithromycin":  {"use": "Bacterial infections",                              "warnings": "Take on empty stomach. Complete full course.",          "common_brands": "Azee, Zithromax"},
    "diclofenac":    {"use": "Strong pain relief and anti-inflammatory",          "warnings": "Take after meals to prevent stomach ulcers.",           "common_brands": "Voveran, Reactin"},
}

PRESCRIPTION_SYSTEM_PROMPT = """You are a medical prescription reading expert.
Extract medicine information from OCR text. Rules:
1. Fix obvious typos based on medical knowledge.
2. Never invent medicines not present in the text.
3. Output 'Unknown' for truly unreadable fields.
4. Follow the EXACT output format. No extra commentary."""

GROQ_VISION_PROMPT = """You are a medical OCR expert. Read this handwritten prescription image carefully.
Extract ALL text exactly as written, including any multilingual instructions (like Bengali, Hindi, etc). 
Pay extreme attention to:
- Medicine names (abbreviated or cursive)
- Dosages (mg, ml, mcg)
- Frequency (1+0+1, OD, BD, TDS etc.)
- Doctor and patient names
Return ONLY the raw extracted text. Do not format it into JSON, just transcribe exactly what you see."""

class PrescriptionAgent:
    def process_prescription(self, file_path: str, filename: str, file_type: str) -> PrescriptionExplanation:
        logger.info(f"Processing Rx: {filename} ({file_type})")
        return self._process_pdf(file_path) if file_type == "pdf" else self._process_image(file_path)

    def _process_pdf(self, file_path: str) -> PrescriptionExplanation:
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            raise ValueError("Could not extract text from PDF.")
        return self._structure(text)

    def _process_image(self, file_path: str) -> PrescriptionExplanation:
        try:
            with Image.open(file_path) as img:
                if img.mode not in ("RGB",):
                    img = img.convert("RGB")
                # Enhance image heavily for Groq Vision
                img = ImageEnhance.Contrast(img).enhance(1.5)
                img = ImageEnhance.Sharpness(img).enhance(1.5)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=95)
                b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception as e:
            return self._fallback(f"Could not open image: {e}")

        # ── Step 1: Vision Extraction ──
        ocr_text = groq_service.vision_generate(b64_img, GROQ_VISION_PROMPT)
        
        if len(ocr_text.strip()) < 5:
            return self._fallback("Vision engine could not extract text.")

        # ── Step 2: Structuring Extraction ──
        return self._structure(ocr_text)

    def _structure(self, text: str) -> PrescriptionExplanation:
        sep = "---"
        prompt = (
            f"Read this extracted prescription text. Extract all medicines.\n\n"
            f"{text[:3000]}\n\n"
            f"Output ONLY in this exact format:\n\n"
            f"DOCTOR: [name or Unknown]\n"
            f"PATIENT: [name or Unknown]\n"
            f"DATE: [date or Unknown]\n"
            f"GENERAL: [notes or Unknown]\n"
            f"{sep}\n"
            f"MEDICINE: [name]\n"
            f"DOSAGE: [amount or Unknown]\n"
            f"FREQUENCY: [how often or Unknown]\n"
            f"DURATION: [how long or Unknown]\n"
            f"INSTRUCTIONS: [notes or Unknown]\n\n"
            f"Separate each medicine with {sep}. No extra text."
        )

        response = groq_service.generate(prompt, PRESCRIPTION_SYSTEM_PROMPT, model_type="report")
        return self._parse(response)

    def _parse(self, response: str) -> PrescriptionExplanation:
        doctor = patient = date = general = None
        medicines, invalid = [], {"unknown", "n/a", "", "[medicine name]"}

        for block in response.split("---"):
            med = dosage = freq = dur = instr = None
            is_med = False
            for line in block.strip().splitlines():
                line = line.strip()
                if not line: continue
                u   = line.upper()
                val = line.split(":", 1)[1].strip() if ":" in line else ""
                if   u.startswith("DOCTOR:"):       doctor  = val
                elif u.startswith("PATIENT:"):      patient = val
                elif u.startswith("DATE:"):         date    = val
                elif u.startswith("GENERAL:"):      general = val
                elif u.startswith("MEDICINE:"):     is_med  = True; med   = val
                elif u.startswith("DOSAGE:"):       dosage  = val
                elif u.startswith("FREQUENCY:"):    freq    = val
                elif u.startswith("DURATION:"):     dur     = val
                elif u.startswith("INSTRUCTIONS:"): instr   = val

            if is_med and med and med.lower() not in invalid:
                item = PrescriptionItem(
                    medicine_name=med,
                    dosage      =dosage if dosage and dosage.lower() not in invalid else None,
                    frequency   =freq   if freq   and freq.lower()   not in invalid else None,
                    duration    =dur    if dur    and dur.lower()    not in invalid else None,
                    instructions=instr  if instr  and instr.lower()  not in invalid else None,
                )
                medicines.append(self._enrich(item))

        return PrescriptionExplanation(
            doctor_name=doctor, patient_name=patient, date=date,
            medicines=medicines, general_instructions=general,
            confidence_score=0.95 if medicines else 0.2,
            raw_text=response
        )

    def _enrich(self, med: PrescriptionItem) -> PrescriptionItem:
        name = med.medicine_name.lower()
        for key, info in MEDICINE_DB.items():
            if key in name or name in key:
                med.purpose  = info["use"]
                med.warnings = f"{info['warnings']} | Brands: {info['common_brands']}"
                break
        return med

    def _fallback(self, reason: str) -> PrescriptionExplanation:
        return PrescriptionExplanation(
            confidence_score=0.0,
            general_instructions="Could not read prescription.",
            raw_text=reason
        )

prescription_agent = PrescriptionAgent()