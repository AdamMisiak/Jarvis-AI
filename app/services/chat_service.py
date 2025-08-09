"""Chat service implementation."""

import json
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.models import ChatMessage
from app.schemas.chat import ChatRequest, ChatResponse


class ChatServiceInterface(ABC):
    """Chat service interface for dependency inversion."""
    
    @abstractmethod
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """Process incoming chat message and return response."""
        pass


class DatabaseChatService(ChatServiceInterface):
    """Database-backed implementation of chat service."""
    
    def __init__(self, db_session: AsyncSession, settings: Settings) -> None:
        """Initialize chat service with database session and settings."""
        self.db_session = db_session
        self.settings = settings
        self.agent_name = "Jarvis"  # Static agent name
    
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """Process chat message and generate response."""
        # Save user message
        user_message = await self._save_message(
            content=request.message,
            is_user_message=True,
            metadata=request.context,
        )
        
        # Generate AI response
        response_content = await self._generate_response(
            request.message,
            request.context
        )
        
        # Save AI response
        ai_message = await self._save_message(
            content=response_content,
            is_user_message=False,
            metadata={
                "agent_name": self.agent_name,
                "user_message_id": user_message.id,
            }
        )
        
        return ChatResponse(
            message=response_content,
            timestamp=ai_message.timestamp,
            metadata={
                "agent_name": self.agent_name,
                "message_id": ai_message.id,
            }
        )
    
    async def _save_message(
        self,
        content: str,
        is_user_message: bool,
        metadata: Optional[dict] = None,
    ) -> ChatMessage:
        """Save message to database."""
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
        """Generate AI response (placeholder implementation)."""
        # This is where you'd integrate with OpenAI, Anthropic, etc.
        # For now, simple echo with agent personality
        
        responses = [
            f"Hello! I'm {self.agent_name}. You said: '{message}'",
            f"As your personal AI agent {self.agent_name}, I understand you mentioned: '{message}'",
            f"Interesting! {self.agent_name} here - I'm processing your message about: '{message}'",
        ]
        
        # Simple selection based on message length
        response_idx = len(message) % len(responses)
        base_response = responses[response_idx]
        
        # Add context if available
        if context:
            base_response += f" (Context: {context})"
        
        # Ensure response doesn't exceed max length
        if len(base_response) > self.settings.max_response_length:
            base_response = base_response[:self.settings.max_response_length - 3] + "..."
        
        return base_response 