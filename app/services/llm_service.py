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
    
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """Main method for chat completion requests - no tracing (handled by caller)."""
        try:
            response_data = await self._make_openai_request(
                messages=request.messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            return LLMResponse(
                content=response_data["choices"][0]["message"]["content"].strip(),
                model=response_data["model"],
                usage=response_data.get("usage"),
                metadata=request.metadata
            )
        except Exception as e:
            raise Exception(f"LLM chat completion failed: {str(e)}")
    
    @observe(name="llm_generate_response")
    async def generate_response(
        self,
        message: str,
        context: Optional[dict] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE
    ) -> str:
        """Simplified method for generating responses - crucial operation to trace."""
        if context:
            user_content = f"Message: {message}\nContext: {json.dumps(context, ensure_ascii=False)}"
        else:
            user_content = message

        messages = [
            {"role": "system", "content": BASE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        request = LLMRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            metadata={
                "user_message": message,
                "context": context,
                "service": "jarvis_ai"
            }
        )
        
        response = await self.chat_completion(request)
        
        # Apply length limit
        max_len = max(1, int(self.settings.max_response_length))
        if len(response.content) > max_len:
            response.content = response.content[: max_len - 3] + "..."
        
        return response.content
    
    async def _make_openai_request(
        self,
        messages: List[Dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ):
        """Low-level method for making OpenAI API requests via HTTP - no tracing needed."""
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
    
    def create_messages(
        self,
        user_message: str,
        system_prompt: str = BASE_SYSTEM_PROMPT,
        context: Optional[dict] = None
    ) -> List[Dict[str, str]]:
        """Helper method to create properly formatted messages - no tracing needed."""
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            user_content = f"Message: {user_message}\nContext: {json.dumps(context, ensure_ascii=False)}"
        else:
            user_content = user_message
            
        messages.append({"role": "user", "content": user_content})
        return messages
    
