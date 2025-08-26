"""LLM service implementation using OpenAI GPT-4o via HTTP requests with essential Langfuse tracing."""

import json
from typing import Optional, Dict, Any, List

import httpx
from langfuse import observe
from app.config.settings import Settings
from app.prompts import BASE_SYSTEM_PROMPT
from app.schemas import LLMRequest, LLMResponse

# Constants
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MODEL = "gpt-4o"
DEFAULT_MAX_TOKENS = 4000
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
REQUEST_TIMEOUT = 30.0


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.api_key = settings.openai_api_key
    
    @observe(name="llm_request")
    async def generate_response(
        self,
        message: str,
        context: Optional[dict] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE
    ) -> str:
        if context:
            user_content = f"Message: {message}\nContext: {json.dumps(context, ensure_ascii=False)}"
        else:
            user_content = message

        messages = [
            {"role": "system", "content": BASE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        response_data = await self._make_openai_request(
            messages=messages,
            model=model,
            temperature=temperature
        )
        
        content = response_data["choices"][0]["message"]["content"].strip()
        
        return content
    
    async def _make_openai_request(
        self,
        messages: List[Dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                OPENAI_API_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    
