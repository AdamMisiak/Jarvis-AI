"""Chat message schemas."""

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
