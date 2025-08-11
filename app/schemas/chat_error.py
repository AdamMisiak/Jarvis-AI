"""Chat error schema."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatError(BaseModel):
    """Chat error schema."""
    
    error: str
    code: str
    timestamp: datetime = Field(default_factory=datetime.now)
