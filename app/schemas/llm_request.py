"""LLM request schema."""

from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class LLMRequest(BaseModel):
    """LLM request schema."""
    
    messages: List[Dict[str, str]] = Field(..., min_items=1)
    model: str = Field(default="gpt-4o")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, gt=0, le=4096)
    metadata: Optional[Dict[str, Any]] = None
