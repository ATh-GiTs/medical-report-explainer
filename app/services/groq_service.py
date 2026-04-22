import httpx
from app.core.config import settings
from app.core.logger import logger

class GroqService:
    """Unified service to handle all LLM and Vision tasks via Groq Cloud."""
    
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    def is_connected(self) -> bool:
        """Checks if the API Key is present for connectivity."""
        return bool(self.api_key)

    def generate(self, prompt: str, system_prompt: str = "", model_type: str = "report", temperature: float = 0.1) -> str:
        """Handles pure text reasoning tasks (RAG and Extraction)."""
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not set in environment.")

        # Select model based on task priority
        model = settings.groq_text_model if model_type == "report" else settings.groq_fast_model
        logger.info(f"Generating with Groq: {model}")

        payload = {
            "model": model,
            "temperature": temperature,
            "max_tokens": 1024,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = httpx.post(
                self.base_url,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise RuntimeError(f"Engine Failure: {str(e)}")

    def vision_generate(self, base64_img: str, prompt: str) -> str:
        """Handles multimodal image-to-text tasks (Prescriptions)."""
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not set in environment.")
            
        model = settings.groq_vision_model
        logger.info(f"Running Vision Analysis with: {model}")
        
        # ⚠️ CRITICAL: Vision models on Groq do NOT support 'system' roles.
        # The prompt and image must be in a single 'user' message content list.
        payload = {
            "model": model,
            "temperature": 0.1,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url", 
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_img}"
                            }
                        }
                    ]
                }
            ]
        }
        
        try:
            response = httpx.post(
                self.base_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}", 
                    "Content-Type": "application/json"
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                logger.error(f"Groq Vision Error Body: {response.text}")
                
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Groq Vision API error: {e}")
            raise RuntimeError(f"Vision Engine Failure: {str(e)}")

# ─── Singleton ────────────────────────────────────────────
groq_service = GroqService()