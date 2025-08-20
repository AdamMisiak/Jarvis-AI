"""LLM service implementation using OpenAI GPT-4o (based on OpenAIService.ts pattern)."""

import json
from typing import Optional, Dict, Any, List

import openai
from app.config.settings import Settings
from app.prompts import BASE_SYSTEM_PROMPT
from app.schemas import LLMRequest, LLMResponse

# Constants
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MODEL = "gpt-4o"
DEFAULT_MAX_TOKENS = 4000


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
    
    async def chat_completion(self, request: LLMRequest) -> LLMResponse:
        """Main method for chat completion requests (similar to OpenAIService.ts)."""
        try:
            response = await self._make_openai_request(
                messages=request.messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            return LLMResponse(
                content=response.choices[0].message.content.strip(),
                model=response.model,
                usage=response.usage.model_dump() if response.usage else None,
                metadata=request.metadata
            )
        except Exception as e:
            raise Exception(f"LLM chat completion failed: {str(e)}")
    
    async def generate_response(
        self,
        message: str,
        context: Optional[dict] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE
    ) -> str:
        """Simplified method for generating responses."""
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
        """Low-level method for making OpenAI API requests."""
        return self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def create_messages(
        self,
        user_message: str,
        system_prompt: str = BASE_SYSTEM_PROMPT,
        context: Optional[dict] = None
    ) -> List[Dict[str, str]]:
        """Helper method to create properly formatted messages."""
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            user_content = f"Message: {user_message}\nContext: {json.dumps(context, ensure_ascii=False)}"
        else:
            user_content = user_message
            
        messages.append({"role": "user", "content": user_content})
        return messages
    
