import httpx
from app.core.config import settings
from app.core.logger import logger


class OllamaService:
    """
    Handles all communication with the local Ollama server.
    Uses dedicated models for different tasks:
    - MedGemma  → medical reports & Q&A
    - llama3.2-vision → prescription image reading
    - llama3.2:3b → fast tasks (classification, translation)
    """

    def __init__(self):
        self.base_url = settings.ollama_base_url

        # ─── Dedicated models per task ────────────────────
        self.report_model = settings.ollama_report_model
        self.vision_model = settings.ollama_vision_model
        self.fast_model = settings.ollama_fast_model

        # ─── Legacy fallback ──────────────────────────────
        self.model = settings.ollama_model
        self.fallback_model = settings.ollama_fallback_model

    def is_connected(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = httpx.get(f"{self.base_url}", timeout=3)
            return response.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model_type: str = "report",
        temperature: float = 0.3,
    ) -> str:
        """
        Send a prompt to Ollama using the right model for the task.

        model_type options:
        - "report"  → MedGemma (best for medical Q&A)
        - "fast"    → llama3.2:3b (best for classification, translation)
        - "vision"  → llama3.2-vision (only for image tasks)
        """
        # ─── Select correct model ─────────────────────────
        model = self._select_model(model_type)
        logger.info(f"Using model: {model} (task: {model_type})")

        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": 1024,
            }
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            result = response.json().get("response", "").strip()
            logger.info(f"Response from {model}: {len(result)} chars")
            return result

        except httpx.TimeoutException:
            logger.warning(f"Timeout with {model} — trying fast model as fallback")
            if model_type != "fast":
                return self.generate(
                    prompt,
                    system_prompt,
                    model_type="fast",
                    temperature=temperature
                )
            raise TimeoutError("Ollama is not responding. Make sure it is running.")

        except Exception as e:
            logger.error(f"Ollama error with {model}: {e}")
            if model_type != "fast":
                logger.info("Falling back to fast model...")
                return self.generate(
                    prompt,
                    system_prompt,
                    model_type="fast",
                    temperature=temperature
                )
            raise RuntimeError(f"Could not get response from Ollama: {e}")

    def _select_model(self, model_type: str) -> str:
        """Return the correct model name for the given task type."""
        model_map = {
            "report": self.report_model,   # MedGemma for medical reports
            "fast": self.fast_model,        # llama3.2:3b for quick tasks
            "vision": self.vision_model,    # llama3.2-vision for images
        }
        return model_map.get(model_type, self.report_model)


# ─── Singleton ────────────────────────────────────────────
ollama_service = OllamaService()
