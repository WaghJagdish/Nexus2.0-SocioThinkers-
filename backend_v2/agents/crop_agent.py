from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from core.logging import get_logger
from core.domain import (
    CropRecommendation,
    CropType,
    WeatherData,
    SoilData,
    LanguageCode,
)
from services.llm_service import LLMService
from services.weather_service import WeatherService
from services.weather_service import GISService

logger = get_logger(__name__)

CROP_DATABASE = {
    CropType.RICE: {
        "temp_range": (20, 35),
        "rainfall_range": (1000, 2000),
        "soil_texture_range": (3, 5),
        "soil_depth_range": (60, 150),
        "ph_range": (5.5, 7.0),
        "season": "Kharif (June-November)",
        "max_variance": {
            "rainfall": 600.0,
            "temperature": 12.0,
            "texture": 2.0,
        }
    },
    CropType.WHEAT: {
        "temp_range": (12, 25),
        "rainfall_range": (450, 800),
        "soil_texture_range": (2, 4),
        "soil_depth_range": (45, 120),
        "ph_range": (6.0, 7.5),
        "season": "Rabi (October-March)",
        "max_variance": {
            "rainfall": 300.0,
            "temperature": 10.0,
            "texture": 2.0,
        }
    },
    CropType.SOYBEAN: {
        "temp_range": (20, 32),
        "rainfall_range": (600, 1000),
        "soil_texture_range": (3, 5),
        "soil_depth_range": (45, 90),
        "ph_range": (6.0, 7.0),
        "season": "Kharif (June-October)",
        "max_variance": {
            "rainfall": 400.0,
            "temperature": 10.0,
            "texture": 2.0,
        }
    },
    CropType.GROUNDNUT: {
        "temp_range": (25, 35),
        "rainfall_range": (500, 750),
        "soil_texture_range": (2, 4),
        "soil_depth_range": (45, 100),
        "ph_range": (6.0, 7.0),
        "season": "Kharif (June-October)",
        "max_variance": {
            "rainfall": 300.0,
            "temperature": 8.0,
            "texture": 2.0,
        }
    },
    CropType.SUGARCANE: {
        "temp_range": (20, 38),
        "rainfall_range": (1200, 2500),
        "soil_texture_range": (3, 5),
        "soil_depth_range": (75, 180),
        "ph_range": (6.0, 8.0),
        "season": "Year-round (12-18 months)",
        "max_variance": {
            "rainfall": 800.0,
            "temperature": 15.0,
            "texture": 2.0,
        }
    },
    CropType.COTTON: {
        "temp_range": (20, 40),
        "rainfall_range": (600, 1000),
        "soil_texture_range": (2, 4),
        "soil_depth_range": (60, 150),
        "ph_range": (6.5, 8.5),
        "season": "Kharif (April-December)",
        "max_variance": {
            "rainfall": 500.0,
            "temperature": 15.0,
            "texture": 2.0,
        }
    },
    CropType.MAIZE: {
        "temp_range": (18, 32),
        "rainfall_range": (500, 800),
        "soil_texture_range": (2, 4),
        "soil_depth_range": (45, 100),
        "ph_range": (5.5, 7.5),
        "season": "Kharif (June-October)",
        "max_variance": {
            "rainfall": 300.0,
            "temperature": 10.0,
            "texture": 2.0,
        }
    },
    CropType.MUSTARD: {
        "temp_range": (10, 25),
        "rainfall_range": (300, 500),
        "soil_texture_range": (1, 3),
        "soil_depth_range": (30, 75),
        "ph_range": (6.0, 8.0),
        "season": "Rabi (October-February)",
        "max_variance": {
            "rainfall": 200.0,
            "temperature": 10.0,
            "texture": 2.0,
        }
    },
}

TEXTURE_ENCODING = {
    "sandy": 1.0,
    "loamy sand": 2.0,
    "sandy_loam": 3.0,
    "sandy loam": 3.0,
    "laterite": 3.0,
    "clay": 3.0,
    "clayey": 3.0,
    "silty_loam": 4.0,
    "silty loam": 4.0,
    "clay_loam": 4.0,
    "clay loam": 4.0,
    "silty_clay": 4.5,
    "silty clay": 4.5,
    "alluvial": 5.0,
    "loam": 5.0,
    "loamy": 5.0,
    "unknown": 3.0,
}

DEPTH_ENCODING = {
    "shallow": 1.0,
    "medium": 2.0,
    "deep": 3.0,
    "very deep": 4.0,
    "unknown": 2.0,
}

AHP_RAW_WEIGHTS = {
    "rainfall": 0.31,
    "temperature": 0.22,
    "soil_depth": 0.15,
    "soil_drainage": 0.11,
    "soil_texture": 0.08,
    "humidity": 0.08,
    "ph": 0.05,
}

RAW_WEIGHT_SUM = sum(AHP_RAW_WEIGHTS.values())
AHP_NORMALIZED_WEIGHTS = {k: v / RAW_WEIGHT_SUM for k, v in AHP_RAW_WEIGHTS.items()}


class CropRecommendationRequest(BaseModel):
    latitude: float
    longitude: float
    language: LanguageCode = LanguageCode.HINDI


class CropSowingAgent:
    def __init__(
        self,
        llm_service: LLMService,
        weather_service: WeatherService,
        gis_service: GISService,
    ):
        self.llm = llm_service
        self.weather = weather_service
        self.gis = gis_service

    async def recommend_crops(
        self,
        request: CropRecommendationRequest,
    ) -> List[CropRecommendation]:
        logger.info(f"Recommending crops for ({request.latitude}, {request.longitude})")

        weather = await self.weather.fetch_weather(request.latitude, request.longitude)
        soil = await self.gis.fetch_soil_data(request.latitude, request.longitude)

        features = self._process_features(weather, soil)
        scores = self._calculate_ahp_suitability(features)
        
        recommendations = [
            CropRecommendation(
                crop_name=crop,
                confidence_score=score["confidence"],
                season=CROP_DATABASE[crop]["season"],
                suitability_factors=score["factors"],
                reasoning="",
            )
            for crop, score in scores[:3]
        ]

        if recommendations:
            reasoning = await self._generate_reasoning(
                recommendations[0],
                weather,
                soil,
                request.language,
                scores[0][1].get("limiting_factor", "None"),
            )
            recommendations[0].reasoning = reasoning

        return recommendations

    def _process_features(self, weather: WeatherData, soil: SoilData) -> Dict[str, Any]:
        # Encode soil texture — try exact match first, then substring
        soil_texture_encoded = 3.0
        soil_texture_lower = soil.soil_texture.value.lower() if hasattr(soil.soil_texture, 'value') else str(soil.soil_texture).lower()
        if soil_texture_lower in TEXTURE_ENCODING:
            soil_texture_encoded = TEXTURE_ENCODING[soil_texture_lower]
        else:
            for key, val in TEXTURE_ENCODING.items():
                if key in soil_texture_lower:
                    soil_texture_encoded = val
                    break

        # Encode soil depth from actual cm value
        soil_depth_encoded = 2.0
        depth_cm = soil.soil_depth_cm if soil.soil_depth_cm else 60.0
        if depth_cm < 50:
            soil_depth_encoded = 1.0
        elif depth_cm < 90:
            soil_depth_encoded = 2.0
        elif depth_cm < 150:
            soil_depth_encoded = 3.0
        else:
            soil_depth_encoded = 4.0

        # Use actual drainage data instead of guessing from texture
        drainage_val = soil.soil_drainage.value.lower() if hasattr(soil.soil_drainage, 'value') else str(soil.soil_drainage).lower()
        drainage_map = {"poor": 1.0, "moderate": 2.0, "good": 3.0, "well": 4.0}
        drainage_encoded = drainage_map.get(drainage_val, 3.0)

        return {
            "rainfall": weather.avg_rainfall_daily_mm * 365,
            "temperature": weather.avg_temp_c,
            "humidity": weather.avg_humidity_pct,
            "soil_texture": soil_texture_encoded,
            "soil_depth": soil_depth_encoded,
            "soil_drainage": drainage_encoded,
            "pH": soil.ph_range,
            "raw_soil_texture": soil.soil_texture,
            "raw_soil_depth": str(soil.soil_depth_cm) + " cm",
        }

    def _calculate_domain_suitability(
        self,
        actual: float,
        optimal_range: Tuple[float, float],
        max_variance: float,
    ) -> float:
        opt_min, opt_max = optimal_range
        if opt_min <= actual <= opt_max:
            return 1.0
        
        deviation = min(abs(actual - opt_min), abs(actual - opt_max))
        score = max(0.0, 1.0 - (deviation / max_variance))
        return score

    def _calculate_ahp_suitability(
        self,
        features: Dict[str, Any],
    ) -> List[Tuple[CropType, Dict[str, Any]]]:
        scores = []

        for crop, specs in CROP_DATABASE.items():
            s_rainfall = self._calculate_domain_suitability(
                features["rainfall"],
                specs["rainfall_range"],
                specs["max_variance"]["rainfall"]
            )

            s_temperature = self._calculate_domain_suitability(
                features["temperature"],
                specs["temp_range"],
                specs["max_variance"]["temperature"]
            )

            s_texture = self._calculate_domain_suitability(
                features["soil_texture"],
                specs["soil_texture_range"],
                specs["max_variance"]["texture"]
            )

            s_depth = min(1.0, features["soil_depth"] / 4.0)
            s_drainage = min(1.0, features["soil_drainage"] / 4.0)
            s_humidity = min(1.0, features["humidity"] / 80.0)

            suitability_score = (
                AHP_NORMALIZED_WEIGHTS["rainfall"] * s_rainfall +
                AHP_NORMALIZED_WEIGHTS["temperature"] * s_temperature +
                AHP_NORMALIZED_WEIGHTS["soil_depth"] * s_depth +
                AHP_NORMALIZED_WEIGHTS["soil_drainage"] * s_drainage +
                AHP_NORMALIZED_WEIGHTS["soil_texture"] * s_texture +
                AHP_NORMALIZED_WEIGHTS["humidity"] * s_humidity
            )

            components = {
                "Rainfall": s_rainfall,
                "Temperature": s_temperature,
                "Soil Texture": s_texture,
                "Soil Depth": s_depth,
            }
            limiting_factor = min(components, key=components.get)

            scores.append(
                (
                    crop,
                    {
                        "confidence": suitability_score,
                        "factors": {
                            "rainfall": s_rainfall,
                            "temperature": s_temperature,
                            "soil_texture": s_texture,
                            "soil_depth": s_depth,
                            "drainage": s_drainage,
                            "humidity": s_humidity,
                        },
                        "limiting_factor": limiting_factor if suitability_score < 0.75 else "None",
                    },
                )
            )

        return sorted(scores, key=lambda x: x[1]["confidence"], reverse=True)

    async def _generate_reasoning(
        self,
        recommendation: CropRecommendation,
        weather: WeatherData,
        soil: SoilData,
        language: LanguageCode,
        limiting_factor: str,
    ) -> str:
        lang_map = {
            LanguageCode.HINDI: "Hindi",
            LanguageCode.MARATHI: "Marathi",
            LanguageCode.ENGLISH: "English",
        }
        language_name = lang_map.get(language, "English")

        system_prompt = f"""You are an agricultural advisor.
CRITICAL: You MUST write your ENTIRE response in the {language_name} language. 
Do NOT output any English text.
Provide a brief, simple explanation of why {recommendation.crop_name.value} is recommended."""

        rainfall_annual = weather.avg_rainfall_daily_mm * 365
        user_prompt = f"""Weather: {weather.avg_temp_c}°C average, {rainfall_annual:.0f}mm annual rainfall
Soil: {soil.soil_texture}, pH {soil.ph_range}, {soil.soil_depth_cm}cm depth

Why is {recommendation.crop_name.value} recommended? (Be concise, 2-3 sentences)"""

        if limiting_factor != "None":
            user_prompt += f"\nNote: {limiting_factor} is a limiting factor that requires management."

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        return await self.llm.invoke(messages)
