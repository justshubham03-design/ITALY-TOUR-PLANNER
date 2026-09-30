"""
Google Gemini LLM Client (Zero External Dependencies).
Connects to Google Generative Language API via standard Python urllib.
"""

import os
import json
import logging
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, List, Any, Optional

logger = logging.getLogger('GeminiClient')

def _load_env_val(key_name: str, default: str = "") -> str:
    val = os.environ.get(key_name, "")
    if not val:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith(f"{key_name}="):
                        val = line.split('=', 1)[1].strip()
                        os.environ[key_name] = val
                        break
    return val or default

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
FALLBACK_GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest"
]
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiClient:
    """
    Client for Google Gemini Generative AI (Gemini 3.8 Flash).
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_GEMINI_MODEL):
        self.api_key = api_key or _load_env_val('GEMINI_API_KEY', '')
        self.model = model or os.environ.get('GEMINI_MODEL', DEFAULT_GEMINI_MODEL)

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def generate_content(self, prompt: str, 
                         system_instruction: Optional[str] = None,
                         model: Optional[str] = None, 
                         temperature: float = 0.3,
                         max_tokens: int = 1000,
                         json_mode: bool = False,
                         timeout: int = 15) -> Dict[str, Any]:
        """
        Generates content using Google Gemini API with multi-model fallback.
        """
        if not self.is_available():
            return {"success": False, "error": "Gemini API key not configured."}

        models_to_try = [model] if model else [self.model] + [m for m in FALLBACK_GEMINI_MODELS if m != self.model]

        for selected_model in models_to_try:
            url = f"{GEMINI_BASE_URL}/{selected_model}:generateContent?key={urllib.parse.quote(self.api_key)}"
            
            payload: Dict[str, Any] = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }

            if system_instruction:
                payload["system_instruction"] = {
                    "parts": [{"text": system_instruction}]
                }

            if json_mode:
                payload["generationConfig"]["responseMimeType"] = "application/json"

            data_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "curl/7.88.1"
                }
            )

            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    candidates = result.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        text = "".join([p.get("text", "") for p in parts])
                        return {
                            "success": True,
                            "content": text,
                            "model": selected_model,
                            "usage": result.get("usageMetadata", {})
                        }
                    else:
                        return {"success": False, "error": "No text candidate returned from Gemini"}
            except urllib.error.HTTPError as e:
                err_body = e.read().decode('utf-8', errors='ignore')
                logger.warning(f"Gemini model '{selected_model}' HTTP error {e.code}: {err_body}")
                continue
            except Exception as e:
                logger.warning(f"Gemini model '{selected_model}' connection error: {str(e)}")
                continue

        return {
            "success": False,
            "error": "All configured Gemini models failed to respond."
        }
