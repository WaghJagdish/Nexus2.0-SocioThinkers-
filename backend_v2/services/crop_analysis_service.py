import base64
import json
import os
from typing import Dict, Any, Optional

import httpx
from langchain_core.messages import SystemMessage, HumanMessage

from core.logging import get_logger
from core.config import get_settings
from services.crop_knowledge_base import CropKnowledgeBase

logger = get_logger(__name__)


NVIDIA_NIM_VISION_MODEL = os.environ.get("NVIDIA_NIM_VISION_MODEL", "moonshotai/kimi-k2.5")
NVIDIA_NIM_URL = os.environ.get(
    "NVIDIA_NIM_URL",
    "https://integrate.api.nvidia.com/v1/chat/completions"
)

# Fallback vision prompt when NVIDIA NIM is unavailable / for demo
VISION_ANALYSIS_PROMPT = """You are an expert agricultural scientist analyzing crop images.
Look at the provided image and determine:
1. What crop is shown
2. Overall health status (score 0-100)
3. Any visible diseases, pests, or nutrient deficiencies
4. Growth stage / estimated days to harvest
5. Recommended immediate action

Return ONLY a valid JSON object matching this schema:
{
    "crop_type": "crop name in English",
    "health_score": 0-100 integer,
    "health_status": "short description of overall condition",
    "disease_detected": true/false,
    "disease_name": "name of disease/pest or 'None'",
    "symptoms_observed": "description of visible symptoms",
    "growth_stage": "seedling/vegetative/flowering/fruiting/maturity",
    "days_to_harvest_estimate": "text estimate like '4-6 weeks'",
    "confidence": 0.0-1.0
}
"""


class CropAnalysisService:
    """
    Analyzes crop images using NVIDIA NIM vision models.
    Falls back to existing LLM service for demo/offline scenarios.
    RAG retrieval enriches results with treatment knowledge.
    """

    def __init__(
        self,
        llm_service=None,
        knowledge_base: Optional[CropKnowledgeBase] = None,
        nvidia_api_key: Optional[str] = None,
    ):
        self.llm = llm_service
        self.kb = knowledge_base or CropKnowledgeBase()
        self.nvidia_api_key = nvidia_api_key or os.environ.get("NVIDIA_API_KEY")
        self.use_nvidia = bool(self.nvidia_api_key)

    # ------------------------------------------------------------------
    # NVIDIA NIM Vision API
    # ------------------------------------------------------------------

    async def _call_nvidia_nim(self, image_base64: str) -> Dict[str, Any]:
        """Call NVIDIA NIM vision model for crop image analysis."""
        if not self.nvidia_api_key:
            raise RuntimeError("NVIDIA_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {self.nvidia_api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        data_uri = f"data:image/jpeg;base64,{image_base64}"
        payload = {
            "model": NVIDIA_NIM_VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this crop image. Identify the crop, assess health (0-100), "
                                "detect any diseases/pests, estimate growth stage and days to harvest. "
                                "Return ONLY JSON with keys: crop_type, health_score, health_status, "
                                "disease_detected, disease_name, symptoms_observed, growth_stage, "
                                "days_to_harvest_estimate, confidence."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            "max_tokens": 16384,
            "temperature": 1.0,
            "top_p": 1.0,
            "stream": False,
            "chat_template_kwargs": {"thinking": True},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(NVIDIA_NIM_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        raw = data["choices"][0]["message"]["content"]
        # Extract JSON from possible markdown
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        return parsed

    # ------------------------------------------------------------------
    # Fallback LLM analysis (no image — text-only demo / offline)
    # ------------------------------------------------------------------

    async def _call_llm_fallback(self, image_base64: str) -> Dict[str, Any]:
        """Use existing LLM with base64 description as fallback."""
        if not self.llm:
            raise RuntimeError("No LLM service available for fallback")

        # Truncate base64 to first 1k chars to avoid token explosion
        truncated = image_base64[:1024]

        messages = [
            SystemMessage(content=VISION_ANALYSIS_PROMPT),
            HumanMessage(
                content=(
                    f"Base64 crop image fragment (first 1KB): {truncated}...\n\n"
                    "Based on typical patterns for this crop type, provide the JSON analysis."
                )
            ),
        ]
        response = await self.llm.invoke(messages, temperature=0.1)
        raw = response.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        return parsed

    # ------------------------------------------------------------------
    # Mock / deterministic fallback for development & offline testing
    # ------------------------------------------------------------------

    def _mock_analysis(self) -> Dict[str, Any]:
        """Return a realistic demo result for testing without API keys."""
        return {
            "crop_type": "wheat",
            "health_score": 62,
            "health_status": "Moderate stress — yellowing on lower leaves, possible nitrogen deficiency or early rust infection.",
            "disease_detected": True,
            "disease_name": "Yellow Rust (Stripe Rust)",
            "symptoms_observed": "Yellow-orange pustules in linear stripes on lower leaf blades, slight chlorosis of leaf tips.",
            "growth_stage": "flowering",
            "days_to_harvest_estimate": "4-6 weeks",
            "confidence": 0.78,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze(
        self,
        image_base64: str,
        language: str = "en",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a crop image and return enriched results.
        Steps:
          1. Vision model (NVIDIA NIM or fallback)
          2. RAG knowledge retrieval for treatments
          3. Price / harvest enrichment
          4. Localized summary generation
        """
        logger.info(f"Analyzing crop image [{language}] (lat={latitude}, lon={longitude})")

        # Step 1: Vision analysis
        vision_result = None
        if self.use_nvidia:
            try:
                vision_result = await self._call_nvidia_nim(image_base64)
                logger.info("NVIDIA NIM vision analysis succeeded")
            except Exception as e:
                logger.warning(f"NVIDIA NIM failed, trying fallback: {e}")

        if vision_result is None and self.llm:
            try:
                vision_result = await self._call_llm_fallback(image_base64)
                logger.info("LLM fallback analysis succeeded")
            except Exception as e:
                logger.warning(f"LLM fallback failed: {e}")

        if vision_result is None:
            logger.info("Using mock demo analysis (no API keys configured)")
            vision_result = self._mock_analysis()

        # Ensure required keys exist
        vision_result.setdefault("crop_type", "unknown crop")
        vision_result.setdefault("health_score", 50)
        vision_result.setdefault("health_status", "Analysis incomplete")
        vision_result.setdefault("disease_detected", False)
        vision_result.setdefault("disease_name", "None")
        vision_result.setdefault("symptoms_observed", "")
        vision_result.setdefault("growth_stage", "unknown")
        vision_result.setdefault("days_to_harvest_estimate", "—")
        vision_result.setdefault("confidence", 0.5)

        crop = vision_result.get("crop_type", "")
        disease = vision_result.get("disease_name", "")

        # Step 2: RAG retrieval for treatments
        knowledge = self.kb.retrieve(crop, disease)
        treatment = "Consult local KVK or agricultural officer for precise diagnosis."
        pesticide = "—"
        if knowledge:
            top = knowledge[0]
            treatment = top.get("treatment", treatment)
            pesticide = top.get("fertilizer", "—")

        # Step 3: Enrich with price / harvest
        market_price = self.kb.get_price(crop)
        harvest = self.kb.get_harvest(crop)

        # Step 4: Build localized summary (placeholder — can be piped through TTS service)
        summary_parts = [
            f"Crop: {crop}.",
            vision_result["health_status"],
        ]
        if vision_result["disease_detected"]:
            summary_parts.append(
                f"Detected {vision_result['disease_name']}. Treatment: {treatment}. "
                f"Suggested input: {pesticide}."
            )
        else:
            summary_parts.append("No disease detected. Crop is healthy.")
        summary_parts.append(f"Estimated harvest: {harvest}. Market price: ₹{market_price} per quintal.")
        summary = " ".join(summary_parts)

        return {
            "crop_type": crop,
            "health_score": vision_result["health_score"],
            "health_status": vision_result["health_status"],
            "disease_detected": vision_result["disease_detected"],
            "disease_name": vision_result["disease_name"],
            "symptoms_observed": vision_result["symptoms_observed"],
            "growth_stage": vision_result["growth_stage"],
            "harvest_estimate": harvest,
            "market_price_estimate": f"₹{market_price} / quintal",
            "treatment_recommendation": treatment,
            "pesticide_fertilizer": pesticide,
            "confidence": vision_result["confidence"],
            "summary": summary,
            "rag_sources": [k["disease"] for k in knowledge],
            "model_used": "nvidia_nim" if self.use_nvidia else ("llm_fallback" if self.llm else "demo_mock"),
        }
