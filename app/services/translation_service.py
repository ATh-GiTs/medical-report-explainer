import os
from deep_translator import GoogleTranslator
from gtts import gTTS
from langdetect import detect
from app.core.config import settings
from app.core.logger import logger


# ─── Language display names for UI ────────────────────────
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "mr": "Marathi (मराठी)",
    "ta": "Tamil (தமிழ்)",
    "bn": "Bengali (বাংলা)",
    "te": "Telugu (తెలుగు)",
    "gu": "Gujarati (ગુજરાતી)",
}


class TranslationService:
    """
    Handles translation of medical explanations into Indian languages
    and optional text-to-speech voice output.
    """

    def translate(self, text: str, target_language: str) -> str:
        """
        Translate text to target language.
        Returns original text if target is English.
        """
        if target_language == "en":
            return text

        try:
            translated = GoogleTranslator(
                source="auto",
                target=target_language
            ).translate(text)
            logger.info(f"Translated to {LANGUAGE_NAMES.get(target_language, target_language)}")
            return translated

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text  # Return original if translation fails

    def detect_language(self, text: str) -> str:
        """Detect the language of input text."""
        try:
            return detect(text)
        except Exception:
            return "en"

    def text_to_speech(self, text: str, language: str, output_dir: str = "./data/logs") -> str | None:
        """
        Convert text to speech and save as MP3.
        Returns path to audio file, or None if failed.
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"voice_{language}.mp3")

            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(output_path)

            logger.info(f"Voice output saved: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Text-to-speech failed: {e}")
            return None

    def get_supported_languages(self) -> dict:
        """Return supported languages for UI display."""
        return LANGUAGE_NAMES


# ─── Singleton ────────────────────────────────────────────
translation_service = TranslationService()
