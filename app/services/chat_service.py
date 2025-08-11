"""LLM service implementation using OpenAI GPT-4o."""

import json
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.models import ChatMessage
from app.schemas import ChatRequest, ChatResponse
from app.prompts import BASE_SYSTEM_PROMPT

# Constants
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_TEMPERATURE = 0.7
REQUEST_TIMEOUT_SECONDS = 30.0


class LLMService:
    def __init__(self, db_session: AsyncSession, settings: Settings) -> None:
        self.db_session = db_session
        self.settings = settings
    
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        user_message = await self._save_message(
            content=request.message,
            is_user_message=True,
            metadata=request.context,
        )
        
        response_content = await self._generate_response(
            request.message,
            request.context
        )
        
        ai_message = await self._save_message(
            content=response_content,
            is_user_message=False,
            metadata={
                "user_message_id": user_message.id,
            }
        )
        
        return ChatResponse(
            message=response_content,
            timestamp=ai_message.timestamp,
            metadata={
                "message_id": ai_message.id,
            }
        )
    
    async def _save_message(
        self,
        content: str,
        is_user_message: bool,
        metadata: Optional[dict] = None,
    ) -> ChatMessage:
        message = ChatMessage(
            content=content,
            is_user_message=is_user_message,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        
        self.db_session.add(message)
        await self.db_session.commit()
        await self.db_session.refresh(message)
        
        return message
    
    async def _generate_response(
        self,
        message: str,
        context: Optional[dict] = None
    ) -> str:
        """Generate AI response using OpenAI GPT-4o."""
        if context:
            user_content = f"Message: {message}\nContext: {json.dumps(context, ensure_ascii=False)}"
        else:
            user_content = message

        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": BASE_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": DEFAULT_TEMPERATURE,
        }

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                resp = await client.post(
                    OPENAI_CHAT_COMPLETIONS_URL,
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
        except Exception:
            text = f"I couldn't reach the AI service. Echoing your message: '{message}'."
        
        max_len = max(1, int(self.settings.max_response_length))
        if len(text) > max_len:
            text = text[: max_len - 3] + "..."
        return text 