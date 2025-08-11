"""Chat request schema."""

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request schema."""
    
    message: str = Field(..., min_length=1, max_length=10000)
    context: Optional[dict] = None
