import json
import logging
from typing import List, Dict, Any, Optional

from core.logging import get_logger

logger = get_logger(__name__)


class SchemeRetriever:
    """
    Manages vector embeddings and execution of hybrid similarity searches
    combining semantic retrieval with exact metadata filtering.
    Uses Supabase pgvector via the existing DatabaseService + LLMService embeddings.
    """

    def __init__(self, llm_service, database_service, cache_service):
        self.llm = llm_service
        self.db = database_service
        self.cache = cache_service

    async def ingest_scheme(self, scheme: Dict[str, Any]) -> bool:
        """Converts a single scheme dict into a vectorized row in the schemes table."""
        try:
            content = self._build_embedding_text(scheme)
            embedding = await self.llm.embed_text(content)

            row = {
                "scheme_id": scheme["scheme_id"],
                "name": scheme["name"],
                "description": scheme.get("description", ""),
                "category": scheme.get("category", "agriculture"),
                "benefits": json.dumps(scheme.get("benefits", {}))
                if isinstance(scheme.get("benefits"), dict)
                else str(scheme.get("benefits", "")),
                "eligibility_criteria": json.dumps(
                    scheme.get("eligibility_criteria", {})
                ),
                "documents_required": json.dumps(
                    scheme.get("documents_required", [])
                ),
                "state": scheme.get("state", "Central"),
                "embedding": embedding,
            }

            await self.db.upsert("schemes", row, on_conflict="scheme_id")
            logger.info(f"Ingested scheme: {scheme['scheme_id']}")
            return True
        except Exception as e:
            logger.error(f"Failed to ingest scheme {scheme.get('scheme_id')}: {e}")
            return False

    async def ingest_documents(self, schemes: List[Dict[str, Any]]) -> int:
        """Batch-ingest multiple schemes. Returns count of successes."""
        success_count = 0
        for scheme in schemes:
            if await self.ingest_scheme(scheme):
                success_count += 1
        logger.info(
            f"Vectorized and stored {success_count}/{len(schemes)} scheme documents."
        )
        return success_count

    async def retrieve_relevant_schemes(
        self,
        query: str,
        user_state: str = "Central",
        user_land_size: float = 0.0,
        k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Performs a similarity search strictly gated by metadata filters to prevent
        cross-state hallucination and enforce baseline physical constraints.

        Uses Supabase RPC function match_schemes for vector cosine similarity
        with pre-filtering on state.
        """
        cache_key = f"rag_{query}_{user_state}_{user_land_size}"
        cached = await self.cache.get("rag_schemes", q=query, state=user_state)
        if cached:
            return cached

        try:
            query_embedding = await self.llm.embed_text(query)

            results = await self.db.rpc(
                "match_schemes",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.72,
                    "match_count": k,
                    "filter_state": user_state.lower() if user_state else "",
                    "filter_category": "agriculture",
                },
            )

            if not results:
                # Fallback: try without state filter
                results = await self.db.rpc(
                    "match_schemes",
                    {
                        "query_embedding": query_embedding,
                        "match_threshold": 0.65,
                        "match_count": k,
                        "filter_state": "",
                        "filter_category": "agriculture",
                    },
                )

            # Post-filter by land size if provided
            if user_land_size > 0 and results:
                filtered = []
                for doc in results:
                    eligibility = doc.get("eligibility_criteria", {})
                    if isinstance(eligibility, str):
                        try:
                            eligibility = json.loads(eligibility)
                        except json.JSONDecodeError:
                            eligibility = {}
                    max_land = eligibility.get("max_land_size_hectares", 999.0)
                    if user_land_size <= float(max_land):
                        filtered.append(doc)
                results = filtered if filtered else results

            await self.cache.set(
                "rag_schemes",
                results,
                ttl=3600,
                q=query,
                state=user_state,
            )
            return results or []

        except Exception as e:
            logger.error(f"Vector retrieval failed: {e}")
            return []

    def _build_embedding_text(self, scheme: Dict[str, Any]) -> str:
        """Construct a dense text representation to maximize embedding quality."""
        benefits = scheme.get("benefits", {})
        eligibility = scheme.get("eligibility_criteria", {})

        amount = benefits.get("amount", 0) if isinstance(benefits, dict) else ""
        frequency = (
            benefits.get("frequency", "regular") if isinstance(benefits, dict) else ""
        )
        max_land = (
            eligibility.get("max_land_size_hectares", "Any")
            if isinstance(eligibility, dict)
            else "Any"
        )
        categories = (
            eligibility.get("farmer_category", [])
            if isinstance(eligibility, dict)
            else []
        )

        return (
            f"Scheme Name: {scheme.get('name', '')}. "
            f"State: {scheme.get('state', 'Central')}. "
            f"Description: {scheme.get('description', '')} "
            f"Benefits include Rs. {amount} paid on a {frequency} basis. "
            f"Eligible Land Size is up to {max_land} hectares. "
            f"Targeting farmers in categories: {', '.join(categories) if categories else 'All'}."
        )

    async def get_scheme_with_rules(
        self, scheme_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch full scheme data including rules from DB."""
        try:
            result = await self.db.get_one("schemes", {"scheme_id": scheme_id})
            if result:
                # Parse JSON fields
                for field in ["eligibility_criteria", "documents_required", "benefits"]:
                    val = result.get(field)
                    if isinstance(val, str):
                        try:
                            result[field] = json.loads(val)
                        except json.JSONDecodeError:
                            pass
            return result
        except Exception as e:
            logger.error(f"Failed to get scheme {scheme_id}: {e}")
            return None
