import fitz  # PyMuPDF
import os
from pathlib import Path
from app.core.logger import logger


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract all text from a PDF file using PyMuPDF.
    Handles multi-page PDFs cleanly.
    """
    try:
        doc = fitz.open(file_path)
        full_text = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            if text.strip():
                full_text.append(f"--- Page {page_num + 1} ---\n{text}")

        doc.close()
        extracted = "\n\n".join(full_text)
        logger.info(f"Extracted {len(extracted)} characters from {Path(file_path).name}")
        return extracted

    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise ValueError(f"Could not read PDF file: {e}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks for RAG ingestion.
    Overlap ensures context is not lost at chunk boundaries.
    """
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    logger.info(f"Created {len(chunks)} chunks from text")
    return chunks


def save_uploaded_file(file_bytes: bytes, filename: str, upload_dir: str) -> str:
    """
    Save an uploaded file to disk and return the full path.
    """
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    logger.info(f"Saved uploaded file: {filename}")
    return file_path
