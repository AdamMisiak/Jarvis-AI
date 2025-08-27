"""Web search service implementation with intelligent decision making."""

import json
import re
from typing import Optional, Dict, Any, List

from langfuse import observe

from app.config.settings import Settings
from app.services.llm_service import LLMService
from app.prompts.search import WEB_SEARCH_DETECTOR_PROMPT


class WebSearchService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm_service = LLMService(settings)
    
    @observe(name="web_search_decision")
    async def is_web_search_needed(self, user_message: str) -> bool:
        messages = [
            {"role": "system", "content": WEB_SEARCH_DETECTOR_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        response = await self.llm_service.generate_response(
            message=f"USER: {user_message}",
            context={"system_prompt": WEB_SEARCH_DETECTOR_PROMPT},
            model="gpt-4o-mini"
        )
        
        response_clean = response.strip()
        print(response_clean)
        
        if response_clean == "1":
            return True
        elif response_clean == "0":
            return False
            

