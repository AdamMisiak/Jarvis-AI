"""Chat API schemas (Pydantic models)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    """Chat message creation schema."""
    
    content: str = Field(..., min_length=1, max_length=10000)
    metadata: Optional[dict] = None


class ChatMessageResponse(BaseModel):
    """Chat message response schema."""
    
    id: int
    content: str
    is_user_message: bool
    timestamp: datetime
    metadata: Optional[dict] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Chat request schema."""
    
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """Chat response schema."""
    
    message: str
    session_id: str
    timestamp: datetime
    metadata: Optional[dict] = None


class ChatSessionResponse(BaseModel):
    """Chat session with messages response schema."""
    
    id: str
    created_at: datetime
    messages: list[ChatMessageResponse] = []

    class Config:
        from_attributes = True


class ChatError(BaseModel):
    """Chat error schema."""
    
    error: str
    code: str
    timestamp: datetime = Field(default_factory=datetime.now) 