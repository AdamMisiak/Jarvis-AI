"""Chat response schema."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """Chat response schema."""
    
    message: str
    timestamp: datetime
    metadata: Optional[dict] = None
