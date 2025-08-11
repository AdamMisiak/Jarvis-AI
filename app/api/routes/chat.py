"""Chat API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.database.connection import get_db_session
from app.schemas import ChatError, ChatRequest, ChatResponse
from app.services.chat_service import LLMService

router = APIRouter(tags=["chat"])


def get_chat_service(
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> LLMService:
    return LLMService(db_session, settings)


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
    chat_service: Annotated[LLMService, Depends(get_chat_service)]
) -> ChatResponse:
    try:
        response = await chat_service.process_message(request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e), "code": "INVALID_REQUEST"}
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "code": "INTERNAL_ERROR"}
        )


 