"""Chat service implementation."""

import json
import uuid
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.settings import Settings
from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionResponse


class ChatServiceInterface(ABC):
    """Chat service interface for dependency inversion."""
    
    @abstractmethod
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """Process incoming chat message and return response."""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[ChatSessionResponse]:
        """Get chat session with messages."""
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
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        session = await self._get_or_create_session(session_id)
        
        # Save user message
        user_message = await self._save_message(
            session_id=session_id,
            content=request.message,
            is_user_message=True,
            metadata=request.context,
        )
        
        # Generate AI response
        response_content = await self._generate_response(
            request.message,
            session_id,
            request.context
        )
        
        # Save AI response
        ai_message = await self._save_message(
            session_id=session_id,
            content=response_content,
            is_user_message=False,
            metadata={
                "agent_name": self.agent_name,
                "user_message_id": user_message.id,
            }
        )
        
        # Count messages in session
        message_count = await self._count_session_messages(session_id)
        
        return ChatResponse(
            message=response_content,
            session_id=session_id,
            timestamp=ai_message.timestamp,
            metadata={
                "agent_name": self.agent_name,
                "message_count": message_count,
                "message_id": ai_message.id,
            }
        )
    
    async def get_session(self, session_id: str) -> Optional[ChatSessionResponse]:
        """Get chat session with messages."""
        stmt = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        result = await self.db_session.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        return ChatSessionResponse.from_orm(session)
    
    async def _get_or_create_session(self, session_id: str) -> ChatSession:
        """Get existing session or create new one."""
        stmt = select(ChatSession).where(ChatSession.id == session_id)
        result = await self.db_session.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            session = ChatSession(id=session_id)
            self.db_session.add(session)
            await self.db_session.commit()
            await self.db_session.refresh(session)
        
        return session
    
    async def _save_message(
        self,
        session_id: str,
        content: str,
        is_user_message: bool,
        metadata: Optional[dict] = None,
    ) -> ChatMessage:
        """Save message to database."""
        message = ChatMessage(
            session_id=session_id,
            content=content,
            is_user_message=is_user_message,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        
        self.db_session.add(message)
        await self.db_session.commit()
        await self.db_session.refresh(message)
        
        return message
    
    async def _count_session_messages(self, session_id: str) -> int:
        """Count messages in session."""
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id)
        result = await self.db_session.execute(stmt)
        messages = result.scalars().all()
        return len(messages)
    
    async def _generate_response(
        self,
        message: str,
        session_id: str,
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