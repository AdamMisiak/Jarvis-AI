"""Chat API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.database.connection import get_db_session
from app.schemas.chat import ChatError, ChatRequest, ChatResponse, ChatSessionResponse
from app.services.chat_service import ChatServiceInterface, DatabaseChatService

router = APIRouter(tags=["chat"])


def get_chat_service(
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> ChatServiceInterface:
    """Dependency injection for chat service."""
    return DatabaseChatService(db_session, settings)


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send message to AI agent",
    description="Send a message to the Jarvis AI agent and receive a response",
    responses={
        200: {"description": "Successful response from agent"},
        400: {"description": "Invalid request", "model": ChatError},
        500: {"description": "Internal server error", "model": ChatError},
    }
)
async def chat(
    request: ChatRequest,
    chat_service: Annotated[ChatServiceInterface, Depends(get_chat_service)]
) -> ChatResponse:
    """Process chat message and return AI agent response."""
    try:
        response = await chat_service.process_message(request)
        return response
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e), "code": "INVALID_REQUEST"}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "code": "INTERNAL_ERROR"}
        )


@router.get(
    "/chat/sessions/{session_id}",
    response_model=ChatSessionResponse,
    summary="Get chat session",
    description="Retrieve a chat session with all messages"
)
async def get_chat_session(
    session_id: str,
    chat_service: Annotated[ChatServiceInterface, Depends(get_chat_service)]
) -> ChatSessionResponse:
    """Get chat session with messages."""
    session = await chat_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Session not found", "code": "SESSION_NOT_FOUND"}
        )
    
    return session 