"""
Multi-LLM Router & Orchestrator (Groq + Gemini Hybrid Engine).
Intelligently routes reasoning and concierge tasks across Groq and Google Gemini.
"""

import logging
from typing import Dict, List, Any, Optional
from agent.groq_client import GroqClient
from agent.gemini_client import GeminiClient

logger = logging.getLogger('LLMRouter')


class LLMRouter:
    """
    Hybrid multi-LLM orchestrator coordinating Groq and Google Gemini.
    """

    def __init__(self, groq_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        self.groq_client = GroqClient(api_key=groq_api_key)
        self.gemini_client = GeminiClient(api_key=gemini_api_key)

    def get_status(self) -> Dict[str, Any]:
        groq_ok = self.groq_client.is_available()
        gemini_ok = self.gemini_client.is_available()
        return {
            "groq_connected": groq_ok,
            "gemini_connected": gemini_ok,
            "groq_model": self.groq_client.model,
            "gemini_model": self.gemini_client.model,
            "active_engine": "Hybrid (Groq + Gemini)" if (groq_ok and gemini_ok) else ("Groq Cloud" if groq_ok else ("Google Gemini" if gemini_ok else "Deterministic Engine"))
        }

    def chat_concierge(self, prompt: str, 
                       system_instruction: str = "You are Viaggio Italia AI Concierge.",
                       preferred_provider: str = "auto", 
                       max_tokens: int = 250) -> Dict[str, Any]:
        """
        Routes conversational concierge requests based on user preference or latency optimization.
        """
        provider = preferred_provider.lower().strip()

        # Route 1: Explicit Groq request
        if provider == "groq":
            if self.groq_client.is_available():
                res = self.groq_client.chat_completion([
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ], max_tokens=max_tokens)
                if res.get("success"):
                    return {"success": True, "content": res["content"], "provider": "Groq", "model": res.get("model")}
            # Fallback to Gemini
            if self.gemini_client.is_available():
                res = self.gemini_client.generate_content(prompt, system_instruction=system_instruction, max_tokens=max_tokens)
                if res.get("success"):
                    return {"success": True, "content": res["content"], "provider": "Gemini (Fallback)", "model": res.get("model")}

        # Route 2: Explicit Gemini request
        elif provider == "gemini":
            if self.gemini_client.is_available():
                res = self.gemini_client.generate_content(prompt, system_instruction=system_instruction, max_tokens=max_tokens)
                if res.get("success"):
                    return {"success": True, "content": res["content"], "provider": "Gemini", "model": res.get("model")}
            # Fallback to Groq
            if self.groq_client.is_available():
                res = self.groq_client.chat_completion([
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ], max_tokens=max_tokens)
                if res.get("success"):
                    return {"success": True, "content": res["content"], "provider": "Groq (Fallback)", "model": res.get("model")}

        # Route 3: Hybrid Auto (Try Groq first for sub-second speed, then Gemini)
        else:
            if self.groq_client.is_available():
                res = self.groq_client.chat_completion([
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ], max_tokens=max_tokens)
                if res.get("success"):
                    return {"success": True, "content": res["content"], "provider": "Groq", "model": res.get("model")}

            if self.gemini_client.is_available():
                res = self.gemini_client.generate_content(prompt, system_instruction=system_instruction, max_tokens=max_tokens)
                if res.get("success"):
                    return {"success": True, "content": res["content"], "provider": "Gemini", "model": res.get("model")}

        return {
            "success": False,
            "error": "No LLM provider responded. Using deterministic calculation."
        }
