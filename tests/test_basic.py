"""
Basic tests for Medical Report Explainer.
Run with: pytest tests/
"""
import pytest
from app.core.config import settings
from app.services.ollama_service import ollama_service
from app.services.translation_service import translation_service


def test_settings_loaded():
    """Test that settings load correctly from config."""
    assert settings.app_name == "Medical Report Explainer"
    assert settings.ollama_model == "alibayram/medgemma"
    assert "en" in settings.supported_languages
    assert "hi" in settings.supported_languages
    assert "mr" in settings.supported_languages


def test_ollama_connection():
    """Test that Ollama is running and reachable."""
    is_connected = ollama_service.is_connected()
    assert is_connected, "Ollama is not running! Start it with: ollama serve"


def test_translation_english():
    """Test that English returns unchanged text."""
    original = "Your blood sugar is normal."
    result = translation_service.translate(original, "en")
    assert result == original


def test_translation_hindi():
    """Test Hindi translation works."""
    original = "Your blood sugar is normal."
    result = translation_service.translate(original, "hi")
    assert result != original  # Should be different (translated)
    assert len(result) > 0


def test_supported_languages():
    """Test all expected languages are supported."""
    languages = translation_service.get_supported_languages()
    assert "en" in languages
    assert "hi" in languages
    assert "mr" in languages


def test_chunk_text():
    """Test that text chunking works correctly."""
    from app.utils.pdf_parser import chunk_text
    sample_text = " ".join(["word"] * 1000)
    chunks = chunk_text(sample_text, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    assert all(len(chunk) > 0 for chunk in chunks)
