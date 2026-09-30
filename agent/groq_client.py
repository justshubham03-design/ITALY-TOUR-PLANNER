"""
Groq LLM Client (OpenAI-compatible, Zero External Dependencies).
Connects to Groq Cloud API using standard Python urllib.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

logger = logging.getLogger('GroqClient')

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

DEFAULT_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
GROQ_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqClient:
    """
    High-speed LLM client for Groq Cloud.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or _load_env_val('GROQ_API_KEY', '')
        self.model = model or os.environ.get('GROQ_MODEL', DEFAULT_MODEL)

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.startswith('gsk_'))

    def chat_completion(self, messages: List[Dict[str, str]], 
                        model: Optional[str] = None, 
                        temperature: float = 0.3, 
                        json_mode: bool = False,
                        max_tokens: int = 1000,
                        timeout: int = 15) -> Dict[str, Any]:
        """
        Executes a chat completion call to Groq Cloud with multi-model fallback.
        """
        if not self.is_available():
            return {"success": False, "error": "Groq API key not configured."}

        models_to_try = [model] if model else [self.model] + [m for m in FALLBACK_MODELS if m != self.model]

        for selected_model in models_to_try:
            payload: Dict[str, Any] = {
                "model": selected_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            data_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                GROQ_COMPLETIONS_URL,
                data=data_bytes,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "curl/7.88.1"
                }
            )

            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    content = result["choices"][0]["message"]["content"]
                    return {
                        "success": True,
                        "content": content,
                        "model": selected_model,
                        "usage": result.get("usage", {})
                    }
            except urllib.error.HTTPError as e:
                err_body = e.read().decode('utf-8', errors='ignore')
                logger.warning(f"Groq model '{selected_model}' HTTP error {e.code}: {err_body}")
                continue
            except Exception as e:
                logger.warning(f"Groq model '{selected_model}' connection error: {str(e)}")
                continue

        return {
            "success": False,
            "error": "All configured Groq models failed to respond."
        }
