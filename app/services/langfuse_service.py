"""Langfuse tracing service for LLM observability."""

import os
from typing import Optional, Dict, Any
from langfuse import observe, get_client

from app.config.settings import Settings


class LangfuseService:
    """Service for managing Langfuse tracing and observability."""
    
    def __init__(self, settings: Settings) -> None:
        """Initialize Langfuse client with settings."""
        self.settings = settings
        
        # Set environment variables for Langfuse
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host
        
        # Initialize Langfuse client
        self.client = get_client()
    
    def start_trace(
        self,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
    ):
        """Start a new trace for tracking a conversation or workflow."""
        if user_id:
            self.client.update_current_trace(user_id=user_id)
        if session_id:
            self.client.update_current_trace(session_id=session_id)
        if metadata:
            self.client.update_current_trace(metadata=metadata)
        if tags:
            self.client.update_current_trace(tags=tags)
        
        return self.client.start_as_current_span(name=name)
    
    def start_span(
        self,
        name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Start a span within current trace for tracking specific operations."""
        span = self.client.start_as_current_span(name=name)
        if input_data:
            self.client.update_current_span(input=input_data)
        if metadata:
            self.client.update_current_span(metadata=metadata)
        return span
    
    def update_current_span(
        self,
        output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: Optional[str] = None,
    ) -> None:
        """Update current span with output data and metadata."""
        update_data = {}
        if output is not None:
            update_data["output"] = output
        if metadata is not None:
            update_data["metadata"] = metadata
        if level is not None:
            update_data["level"] = level
        
        if update_data:
            self.client.update_current_span(**update_data)
    
    def update_current_trace(
        self,
        output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> None:
        """Update current trace with final output and metadata."""
        update_data = {}
        if output is not None:
            update_data["output"] = output
        if metadata is not None:
            update_data["metadata"] = metadata
        if user_id is not None:
            update_data["user_id"] = user_id
        if session_id is not None:
            update_data["session_id"] = session_id
        if tags is not None:
            update_data["tags"] = tags
            
        if update_data:
            self.client.update_current_trace(**update_data)
    
    def flush(self) -> None:
        """Flush all pending traces to Langfuse."""
        self.client.flush()
    
    def observe_function(self, name: str):
        """Decorator for observing functions."""
        return observe(name=name)
