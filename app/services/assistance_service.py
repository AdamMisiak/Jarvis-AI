"""Assistance service for handling chat logic and orchestrating LLM + Langfuse."""

import json
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from langfuse import observe

from app.models import ChatMessage
from app.schemas import ChatRequest, ChatResponse, LLMRequest, AssistanceContext
from app.services.llm_service import LLMService
from app.services.langfuse_service import LangfuseService
from app.services.web_search_service import WebSearchService
from app.config.settings import Settings


class AssistanceService:
    def __init__(self, db_session: AsyncSession, settings: Settings) -> None:
        self.db_session = db_session
        self.settings = settings
        
        self.llm_service = LLMService(settings)
        self.langfuse_service = LangfuseService(settings)
        self.web_search_service = WebSearchService(settings)
    
    @observe(name="chat_conversation")
    async def handle_chat_message(self, request: ChatRequest, context: Optional[AssistanceContext] = None) -> ChatResponse:
        self.langfuse_service.update_trace(
            metadata={
                "user_message": request.message,
                "context": request.context,
                "service": "jarvis_ai"
            },
            tags=["chat", "conversation"]
        )
        
        try:
            user_message = await self._save_user_message(request)
            
            needs_web_search = await self.web_search_service.is_web_search_needed(request.message)
            
            if needs_web_search:
                print(f"🔍 Web search needed for: {request.message}")
                response_content = "Web search functionality not yet implemented"
            else:
                print(f"📝 No web search needed for: {request.message}")
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
            
            ai_message = await self._save_ai_message(response_content, user_message.id)
            
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
            self.langfuse_service.update_trace(
                output={"error": str(e)},
                metadata={"error_type": type(e).__name__}
            )
            raise
        finally:
            self.langfuse_service.flush()
    
    async def _save_user_message(self, request: ChatRequest) -> ChatMessage:
        return await self._save_message(
            content=request.message,
            is_user_message=True,
            metadata=request.context,
        )
    
    async def _generate_ai_response(self, request: ChatRequest) -> str:
        return await self.llm_service.generate_response(
            request.message,
            request.context
        )
    
    async def _save_ai_message(self, response_content: str, user_message_id: int) -> ChatMessage:
        return await self._save_message(
            content=response_content,
            is_user_message=False,
            metadata={"user_message_id": user_message_id}
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
