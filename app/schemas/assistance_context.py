"""Assistance context schema."""

from typing import Optional, Dict, Any, List

from pydantic import BaseModel


class AssistanceContext(BaseModel):
    """Assistance context schema."""
    
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
