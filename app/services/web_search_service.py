"""Web search service implementation with intelligent decision making."""

import json
import re
from typing import Any, Dict, List, Optional

import httpx
from langfuse import observe

from app.config.settings import Settings
from app.config.constants import RESOURCES
from app.services.llm_service import LLMService
from app.prompts.search import WEB_SEARCH_DETECTOR_PROMPT, build_domain_selection_prompt


class WebSearchService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm_service = LLMService(settings)
        self.resources = RESOURCES

    @observe(name="is_web_search_needed")
    async def is_web_search_needed(self, user_message: str) -> bool:
        print(f"Input (isWebSearchNeeded): {user_message}")
        
        response = await self.llm_service.generate_response(
            message=f"USER: {user_message}",
            context={"system_prompt": WEB_SEARCH_DETECTOR_PROMPT},
            model="gpt-4o-mini"
        )
        
        response_clean = response.strip()
        
        result = response_clean == "1"
        print(f"Output (isWebSearchNeeded): {result}")
        return result

    @observe(name="generate_queries")
    async def generate_queries(self, user_message: str) -> Dict[str, Any]:
        print(f"Input (generateQueries): {user_message}")
        
        prompt = build_domain_selection_prompt()
        response = await self.llm_service.generate_response(
            message=f"USER: {user_message}",
            context={"system_prompt": prompt},
            model="gpt-4o-mini",
            temperature=0.2,
        )

        parsed = json.loads(response)

        if parsed is None:
            print("Error parsing JSON response")
            return {"queries": [], "thoughts": ""}

        all_queries = parsed.get("queries", [])
        filtered_queries = []
        
        for query in all_queries:
            if not isinstance(query, dict):
                continue
                
            query_url = query.get("url", "")
            if any(domain["url"] in query_url for domain in self.resources):
                filtered_queries.append(query)

        result = {
            "thoughts": parsed.get("_thoughts", ""),
            "queries": filtered_queries,
        }

        print(f"Output (generateQueries): {result}")
        return result

    @observe(name="execute_search")
    async def execute_search(self, queries: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        print(f"Input (executeSearch): {queries}")

        all_results = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for query_obj in queries:
                query_text = query_obj.get("q", "")
                domain = query_obj.get("url", "")

                if not query_text or not domain:
                    continue

                search_query = f"site:{domain} {query_text}"

                try:
                    response = await client.post(
                        f"{self.settings.firecrawl_api_url}/v1/search",
                        headers={
                            "Authorization": f"Bearer {self.settings.firecrawl_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "query": search_query,
                            "limit": 6,
                        },
                    )
                    response.raise_for_status()

                    data = response.json()
                    results = data.get("data", [])

                    for result in results:
                        all_results.append({
                            "url": result.get("url", ""),
                            "title": result.get("title", ""),
                            "description": result.get("description", ""),
                        })

                except httpx.HTTPError as e:
                    print(f"Error searching {domain}: {e}")
                    continue

        print(f"Output (executeSearch): {all_results}")
        return all_results

