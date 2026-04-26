from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from core.logging import get_logger
from core.container import get_container
from core.exceptions import ApplicationException

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/crop", tags=["crop-analysis"])


class CropAnalyzeRequest(BaseModel):
    user_id: str
    image_base64: str
    language: str = "en"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CropAnalyzeResponse(BaseModel):
    crop_type: str
    health_score: int
    health_status: str
    disease_detected: bool
    disease_name: str
    symptoms_observed: str
    growth_stage: str
    harvest_estimate: str
    market_price_estimate: str
    treatment_recommendation: str
    pesticide_fertilizer: str
    confidence: float
    summary: str
    rag_sources: list
    model_used: str


@router.post("/analyze", response_model=CropAnalyzeResponse)
async def analyze_crop(request: CropAnalyzeRequest):
    """
    Analyze a crop image using NVIDIA NIM vision + RAG knowledge base.
    Returns health score, disease detection, treatment, harvest and price estimates.
    """
    try:
        container = get_container()
        service = await container.get("crop_analysis_service")

        result = await service.analyze(
            image_base64=request.image_base64,
            language=request.language,
            latitude=request.latitude,
            longitude=request.longitude,
        )
        return CropAnalyzeResponse(**result)

    except ApplicationException as e:
        logger.error(f"Application error in crop analysis: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in crop analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Crop analysis failed")
