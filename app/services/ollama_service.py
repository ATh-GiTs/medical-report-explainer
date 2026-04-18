import httpx
from app.core.config import settings
from app.core.logger import logger


class OllamaService:
    """
    Handles all communication with the local Ollama server.
    Uses MedGemma as primary model, falls back to Llama 3.2 if needed.
    """

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.fallback_model = settings.ollama_fallback_model

    def is_connected(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = httpx.get(f"{self.base_url}", timeout=3)
            return response.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: str = "", use_fallback: bool = False) -> str:
        """
        Send a prompt to Ollama and get a response.
        Automatically falls back to llama3.2 if MedGemma fails.
        """
        model = self.fallback_model if use_fallback else self.model

        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,      # Lower = more factual (good for medical)
                "top_p": 0.9,
                "num_predict": 1024,
            }
        }

        try:
            logger.info(f"Sending prompt to Ollama ({model})")
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300.0  # Medical responses can be detailed
            )
            response.raise_for_status()
            result = response.json().get("response", "").strip()
            logger.info(f"Got response from Ollama ({len(result)} chars)")
            return result

        except httpx.TimeoutException:
            logger.warning(f"Timeout with {model}, trying fallback...")
            if not use_fallback:
                return self.generate(prompt, system_prompt, use_fallback=True)
            raise TimeoutError("Ollama is not responding. Make sure it's running.")

        except Exception as e:
            logger.error(f"Ollama error: {e}")
            if not use_fallback:
                logger.info("Trying fallback model...")
                return self.generate(prompt, system_prompt, use_fallback=True)
            raise RuntimeError(f"Could not get response from Ollama: {e}")


# ─── Singleton ────────────────────────────────────────────
ollama_service = OllamaService()
