"""LLM response schema."""

from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """LLM response schema."""
    
    content: str = Field(..., min_length=1)
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
