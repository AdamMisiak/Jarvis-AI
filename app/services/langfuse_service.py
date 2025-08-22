"""Langfuse tracing service for LLM observability - focused on crucial operations only."""

import os
from typing import Optional, Dict, Any
from contextlib import contextmanager
from langfuse import observe, get_client

from app.config.settings import Settings


class LangfuseService:
    """Service for managing Langfuse tracing - only crucial operations."""
    
    def __init__(self, settings: Settings) -> None:
        """Initialize Langfuse client with settings."""
        self.settings = settings
        
        # Set environment variables for Langfuse
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host
        
        # Initialize Langfuse client
        self.client = get_client()
    
    @contextmanager
    def span(self, name: str, input_data: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for creating spans - only for crucial operations."""
        span = self.client.start_as_current_span(name=name)
        
        if input_data:
            self.client.update_current_span(input=input_data)
        if metadata:
            self.client.update_current_span(metadata=metadata)
        
        try:
            yield span
        finally:
            # Span automatically ends when context exits
            pass
    
    def update_span(self, output: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None, level: Optional[str] = None):
        """Update current span with data."""
        update_data = {}
        if output is not None:
            update_data["output"] = output
        if metadata is not None:
            update_data["metadata"] = metadata
        if level is not None:
            update_data["level"] = level
        
        if update_data:
            self.client.update_current_span(**update_data)
    
    def update_trace(self, **kwargs):
        """Update current trace with metadata."""
        if kwargs:
            self.client.update_current_trace(**kwargs)
    
    def flush(self):
        """Flush all pending traces to Langfuse."""
        self.client.flush()
    
    # Convenience method for the @observe decorator
    def observe(self, name: str):
        """Get the observe decorator for function tracing."""
        return observe(name=name)
