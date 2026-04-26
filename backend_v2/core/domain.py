from typing import Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CropType(str, Enum):
    RICE = "rice"
    WHEAT = "wheat"
    SOYBEAN = "soybean"
    GROUNDNUT = "groundnut"
    SUGARCANE = "sugarcane"
    COTTON = "cotton"
    MAIZE = "maize"
    MUSTARD = "mustard"
    POTATO = "potato"
    TOMATO = "tomato"
    ONION = "onion"
    PULSE = "pulse"


class LanguageCode(str, Enum):
    HINDI = "hi"
    MARATHI = "mr"
    ENGLISH = "en"
    PUNJABI = "pa"
    TAMIL = "ta"
    TELUGU = "te"
    KANNADA = "kn"
    GUJARATI = "gu"
    BENGALI = "bn"
    ODIA = "or"
    MALAYALAM = "ml"


class SoilType(str, Enum):
    CLAYEY = "clayey"
    LOAMY = "loamy"
    SANDY = "sandy"
    ALLUVIAL = "alluvial"
    SANDY_LOAM = "sandy_loam"
    CLAY_LOAM = "clay_loam"
    SILTY_CLAY = "silty_clay"
    SILTY_LOAM = "silty_loam"
    LATERITE = "laterite"


class DrainageType(str, Enum):
    POOR = "poor"
    MODERATE = "moderate"
    GOOD = "good"
    WELL = "well"


@dataclass
class GeoLocation:
    latitude: float
    longitude: float
    state: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "state": self.state,
            "district": self.district,
            "village": self.village,
        }


@dataclass
class WeatherData:
    avg_temp_c: float
    avg_rainfall_daily_mm: float
    avg_humidity_pct: float
    forecast_days: int
    source: str = "open-meteo"
    cached: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "avg_temp_c": self.avg_temp_c,
            "avg_rainfall_daily_mm": self.avg_rainfall_daily_mm,
            "avg_humidity_pct": self.avg_humidity_pct,
            "forecast_days": self.forecast_days,
            "source": self.source,
            "cached": self.cached,
        }


@dataclass
class SoilData:
    soil_texture: SoilType
    soil_depth_cm: float
    soil_drainage: DrainageType
    ph_range: str
    organic_carbon: str
    land_use_class: str
    source: str = "bhuvan"
    is_estimated: bool = False
    cached: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "soil_texture": getattr(self.soil_texture, 'value', self.soil_texture),
            "soil_depth_cm": self.soil_depth_cm,
            "soil_drainage": getattr(self.soil_drainage, 'value', self.soil_drainage),
            "ph_range": self.ph_range,
            "organic_carbon": self.organic_carbon,
            "land_use_class": self.land_use_class,
            "source": self.source,
            "is_estimated": self.is_estimated,
            "cached": self.cached,
        }


@dataclass
class CropRecommendation:
    crop_name: CropType
    confidence_score: float
    season: str
    suitability_factors: dict[str, float]
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "crop_name": self.crop_name.value,
            "confidence_score": self.confidence_score,
            "season": self.season,
            "suitability_factors": self.suitability_factors,
            "reasoning": self.reasoning,
        }


@dataclass
class Scheme:
    id: str
    name: str
    description: str
    eligibility_criteria: List[str]
    benefits: str
    state: Optional[str]
    category: str
    documents_required: List[str]
    contact_info: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "eligibility_criteria": self.eligibility_criteria,
            "benefits": self.benefits,
            "state": self.state,
            "category": self.category,
            "documents_required": self.documents_required,
            "contact_info": self.contact_info,
        }


@dataclass
class FarmerProfile:
    user_id: str
    name: Optional[str] = None
    aadhaar_number: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    mobile_number: Optional[str] = None
    location: Optional[GeoLocation] = None
    land_area_hectares: Optional[float] = None
    primary_crop: Optional[CropType] = None
    preferred_language: LanguageCode = LanguageCode.HINDI
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "aadhaar_number": self.aadhaar_number,
            "bank_account": self.bank_account,
            "bank_ifsc": self.bank_ifsc,
            "mobile_number": self.mobile_number,
            "location": self.location.to_dict() if self.location else None,
            "land_area_hectares": self.land_area_hectares,
            "primary_crop": self.primary_crop.value if self.primary_crop else None,
            "preferred_language": self.preferred_language.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class ProcessingRequest:
    session_id: str
    user_id: str
    request_type: str
    query_text: str
    language: LanguageCode
    location: GeoLocation
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "request_type": self.request_type,
            "query_text": self.query_text,
            "language": self.language.value,
            "location": self.location.to_dict(),
            "created_at": self.created_at.isoformat(),
        }
