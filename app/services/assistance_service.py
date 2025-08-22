"""Assistance service for handling chat logic and orchestrating LLM + Langfuse."""

import json
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from langfuse import observe

from app.models import ChatMessage
from app.schemas import ChatRequest, ChatResponse, LLMRequest, AssistanceContext
from app.services.llm_service import LLMService
from app.services.langfuse_service import LangfuseService
from app.config.settings import Settings


class AssistanceService:
    """Service for handling chat messages with LLM and Langfuse integration."""
    
    def __init__(self, db_session: AsyncSession, settings: Settings) -> None:
        self.db_session = db_session
        self.settings = settings
        
        # Initialize services
        self.llm_service = LLMService(settings)
        self.langfuse_service = LangfuseService(settings)
    
    @observe(name="chat_conversation")
    async def handle_chat_message(self, request: ChatRequest, context: Optional[AssistanceContext] = None) -> ChatResponse:
        """Process a chat message with essential tracing only."""
        # Set trace metadata for the entire conversation
        self.langfuse_service.update_trace(
            metadata={
                "user_message": request.message,
                "context": request.context,
                "service": "jarvis_ai"
            },
            tags=["chat", "conversation"]
        )
        
        try:
            # Save user message (no tracing - not crucial)
            user_message = await self._save_user_message(request)
            
            # Generate AI response (crucial - trace this)
            with self.langfuse_service.span("llm_generation", input_data={
                "message_length": len(request.message),
                "user_message": request.message,
                "context": request.context
            }):
                response_content = await self._generate_ai_response(request)
                self.langfuse_service.update_span(output={
                    "response_length": len(response_content),
                    "response_preview": response_content[:100] + "..." if len(response_content) > 100 else response_content
                })
            
            # Save AI message (no tracing - not crucial)
            ai_message = await self._save_ai_message(response_content, user_message.id)
            
            # Update trace with final result
            self.langfuse_service.update_trace(
                output={
                    "response": response_content,
                    "user_message_id": user_message.id,
                    "ai_message_id": ai_message.id
                }
            )
            
            return ChatResponse(
                message=response_content,
                timestamp=ai_message.timestamp,
                metadata={"message_id": ai_message.id}
            )
            
        except Exception as e:
            # Log error to trace (crucial for debugging)
            self.langfuse_service.update_trace(
                output={"error": str(e)},
                metadata={"error_type": type(e).__name__}
            )
            raise
        finally:
            # Ensure traces are flushed
            self.langfuse_service.flush()
    
    async def _save_user_message(self, request: ChatRequest) -> ChatMessage:
        """Save user message to database - no tracing needed."""
        return await self._save_message(
            content=request.message,
            is_user_message=True,
            metadata=request.context,
        )
    
    async def _generate_ai_response(self, request: ChatRequest) -> str:
        """Generate AI response using LLM service - crucial operation."""
        return await self.llm_service.generate_response(
            request.message,
            request.context
        )
    
    async def _save_ai_message(self, response_content: str, user_message_id: int) -> ChatMessage:
        """Save AI message to database - no tracing needed."""
        return await self._save_message(
            content=response_content,
            is_user_message=False,
            metadata={"user_message_id": user_message_id}
        )
    
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """Backward compatibility method."""
        return await self.handle_chat_message(request)
    
    async def generate_assistance_response(
        self,
        message: str,
        context: Optional[AssistanceContext] = None
    ) -> str:
        """Generate assistance response using LLM service."""
        try:
            # Prepare context for LLM
            llm_context = {}
            if context:
                if context.conversation_history:
                    llm_context["conversation_history"] = context.conversation_history
                if context.metadata:
                    llm_context.update(context.metadata)
            
            # Create LLM request
            messages = self.llm_service.create_messages(
                user_message=message,
                context=llm_context if llm_context else None
            )
            
            llm_request = LLMRequest(
                messages=messages,
                metadata={
                    "assistance_context": context.model_dump() if context else None,
                    "service": "assistance"
                }
            )
            
            # Get response from LLM
            llm_response = await self.llm_service.chat_completion(llm_request)
            return llm_response.content
            
        except Exception as e:
            raise Exception(f"Assistance response generation failed: {str(e)}")
    
    def create_assistance_context(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AssistanceContext:
        """Create assistance context for operations."""
        return AssistanceContext(
            user_id=user_id,
            session_id=session_id,
            conversation_history=conversation_history,
            metadata=metadata
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
