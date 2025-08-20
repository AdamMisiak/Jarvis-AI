"""Assistance service for handling chat logic and orchestrating LLM + Langfuse (based on AssistantService.ts pattern)."""

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
        
        # Initialize independent services
        self.llm_service = LLMService(settings)
        self.langfuse_service = LangfuseService(settings)
    
    @observe(name="chat_conversation")
    async def handle_chat_message(self, request: ChatRequest, context: Optional[AssistanceContext] = None) -> ChatResponse:
        """Process a chat message with full tracing and database operations."""
        # Update trace with conversation metadata
        self.langfuse_service.update_current_trace(
            metadata={
                "user_message": request.message,
                "context": request.context,
                "service": "jarvis_ai"
            },
            tags=["chat", "conversation"]
        )
        
        try:
            # Save user message with span tracking
            with self.langfuse_service.start_span(
                name="save_user_message",
                input_data={"message": request.message, "context": request.context}
            ):
                user_message = await self._save_message(
                    content=request.message,
                    is_user_message=True,
                    metadata=request.context,
                )
                
                self.langfuse_service.update_current_span(
                    output={"message_id": user_message.id},
                    level="INFO"
                )
            
            # Generate response with tracing
            with self.langfuse_service.start_span(
                name="llm_generation",
                input_data={
                    "message": request.message,
                    "context": request.context,
                    "model": "gpt-4o"
                }
            ):
                try:
                    response_content = await self.llm_service.generate_response(
                        request.message,
                        request.context
                    )
                    
                    self.langfuse_service.update_current_span(
                        output={"response": response_content},
                        level="INFO"
                    )
                    
                except Exception as e:
                    self.langfuse_service.update_current_span(
                        output={"error": str(e)},
                        level="ERROR",
                        metadata={"error_type": type(e).__name__}
                    )
                    raise
            
            # Save AI message
            with self.langfuse_service.start_span(
                name="save_ai_message",
                input_data={"response": response_content}
            ):
                ai_message = await self._save_message(
                    content=response_content,
                    is_user_message=False,
                    metadata={
                        "user_message_id": user_message.id,
                    }
                )
                
                self.langfuse_service.update_current_span(
                    output={"message_id": ai_message.id},
                    level="INFO"
                )
            
            # Update trace with final result
            self.langfuse_service.update_current_trace(
                output={
                    "response": response_content,
                    "user_message_id": user_message.id,
                    "ai_message_id": ai_message.id
                }
            )
            
            return ChatResponse(
                message=response_content,
                timestamp=ai_message.timestamp,
                metadata={
                    "message_id": ai_message.id,
                }
            )
            
        except Exception as e:
            # Update trace with error information
            self.langfuse_service.update_current_trace(
                output={"error": str(e)},
                metadata={"error_type": type(e).__name__}
            )
            raise
        finally:
            # Ensure traces are flushed
            self.langfuse_service.flush()
    
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
