import json
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from langchain_core.messages import SystemMessage, HumanMessage

from core.logging import get_logger
from core.domain import Scheme, LanguageCode
from repositories.scheme_repository import SchemeRepository

logger = get_logger(__name__)

class SchemeService:
    def __init__(self, llm_service, cache_service, repo=None):
        self.llm = llm_service
        self.cache = cache_service
        self.repo = repo

    async def search_schemes(
        self,
        query: str,
        state: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5,
        language: str = "en",
    ) -> List[dict]:
        logger.info(f"Searching schemes via Web Scraper: query={query}, state={state}, lang={language}")

        cache_key = f"web_schemes_{query}_{state}_{language}"
        cached = await self.cache.get("schemes", q=query, state=state, lang=language)
        if cached:
            return cached

        try:
            search_query = f"{query} agriculture government schemes {'in ' + state if state else 'India'}"
            ddgs = DDGS()
            results = list(ddgs.text(search_query, max_results=3))
            
            scraped_texts = []
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                for res in results:
                    url = res.get("href")
                    if not url:
                        continue
                    try:
                        resp = await client.get(url)
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        text = soup.get_text(separator=' ', strip=True)
                        scraped_texts.append(f"Source URL: {url}\n{text[:3000]}")
                    except Exception as e:
                        logger.warning(f"Failed to scrape {url}: {e}")

            combined_text = "\n---\n".join(scraped_texts)
            
            lang_map = {
                "hi": "Hindi",
                "mr": "Marathi",
                "en": "English",
            }
            target_language = lang_map.get(language.lower(), "English")
            
            prompt = f"""
            Extract up to {limit} agricultural government schemes from the following text.
            If no specific schemes are found, return general schemes relevant to '{query}' in '{state or 'India'}'.
            Format the response strictly as a JSON array of objects with keys: "id" (string), "name" (string), "benefits" (string), "state" (string), "link" (string, the Source URL where this was found).
            CRITICAL: The string values for "name" and "benefits" MUST BE strictly written in the {target_language} language. DO NOT write them in English.
            Ensure no extra text or markdown formatting outside the JSON array.
            
            TEXT:
            {combined_text[:10000]}
            """
            
            messages = [
                SystemMessage(content="You are an agricultural scheme extractor. Always return valid JSON only."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.invoke(messages, temperature=0.1)
            raw_content = response.strip()
            
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:-3].strip()
            elif raw_content.startswith("```"):
                raw_content = raw_content[3:-3].strip()
                
            parsed_schemes = json.loads(raw_content)
            
            if not isinstance(parsed_schemes, list):
                parsed_schemes = [parsed_schemes]
                
            await self.cache.set("schemes", parsed_schemes, ttl=86400, q=query, state=state, lang=language)
            return parsed_schemes
            
        except Exception as e:
            logger.error(f"Web scraper scheme search failed: {e}")
            return [
                {
                    "id": "fallback-1",
                    "name": "PM-KISAN",
                    "benefits": "₹6000/year direct benefit",
                    "state": state or "all",
                }
            ]

    async def vector_search(
        self,
        embedding: List[float],
        state: Optional[str] = None,
        limit: int = 5,
    ) -> List[dict]:
        if not self.repo:
            logger.warning("vector_search called but no SchemeRepository configured")
            return []
        logger.info(f"Vector searching schemes in {state}")
        return await self.repo.vector_search(
            embedding=embedding,
            state=state,
            limit=limit,
        )

    async def get_scheme(self, scheme_id: str) -> Optional[dict]:
        if not self.repo:
            logger.warning("get_scheme called but no SchemeRepository configured")
            return None
        logger.info(f"Fetching scheme: {scheme_id}")
        return await self.repo.get_by_id(scheme_id)

    async def get_all_states(self) -> List[str]:
        if not self.repo:
            return []
        return await self.repo.get_all_states()
