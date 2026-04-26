from typing import Optional
import asyncio

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import Settings
from core.logging import get_logger
from core.exceptions import ExternalServiceException, TimeoutException
from services.cache_service import CacheService
from core.domain import WeatherData, SoilData, SoilType, DrainageType

logger = get_logger(__name__)


class WeatherService:
    def __init__(self, settings: Settings, cache: CacheService):
        self.settings = settings
        self.cache = cache

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> WeatherData:
        cache_key = f"weather_{round(latitude, 2)}_{round(longitude, 2)}"

        cached = await self.cache.get("weather", lat=latitude, lon=longitude)
        if cached:
            logger.info(f"Weather cache hit for ({latitude}, {longitude})")
            cached_data = cached.copy()
            cached_data["cached"] = True
            return WeatherData(**cached_data)

        try:
            async with httpx.AsyncClient(timeout=self.settings.WEATHER_API_TIMEOUT) as client:
                response = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
                        "hourly": "relative_humidity_2m",
                        "timezone": "Asia/Kolkata",
                        "forecast_days": 7,
                    },
                )
                response.raise_for_status()
                data = response.json()

                daily = data.get("daily", {})
                hourly = data.get("hourly", {})

                temps = daily.get("temperature_2m_max", [])
                avg_temp = sum(temps) / len(temps) if temps else 25.0

                rainfall = daily.get("precipitation_sum", [])
                avg_rainfall = sum(rainfall) / len(rainfall) if rainfall else 5.0

                humidity = hourly.get("relative_humidity_2m", [])
                avg_humidity = sum(humidity) / len(humidity) if humidity else 60.0

                weather_data = {
                    "avg_temp_c": avg_temp,
                    "avg_rainfall_daily_mm": avg_rainfall,
                    "avg_humidity_pct": avg_humidity,
                    "forecast_days": 7,
                }

                await self.cache.set(
                    "weather",
                    weather_data,
                    ttl=self.settings.WEATHER_CACHE_TTL,
                    lat=latitude,
                    lon=longitude,
                )

                return WeatherData(**weather_data)

        except asyncio.TimeoutError:
            logger.error(f"Weather API timeout")
            raise TimeoutException("weather fetch", self.settings.WEATHER_API_TIMEOUT)
        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")
            raise ExternalServiceException("Weather API", str(e))


class GISService:
    """Fetches real soil data from ISRIC SoilGrids v2.0 REST API with
    multi-depth, multi-property queries and USDA texture classification."""

    # ISRIC SoilGrids available depth labels
    DEPTH_LABELS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
    # Mid-point of each depth range in cm (used for weighted averages)
    DEPTH_MID_CM = [2.5, 10.0, 22.5, 45.0, 80.0, 150.0]
    # Properties we request (covers texture, chemistry, density, coarse fragments)
    ISRIC_PROPERTIES = ["clay", "sand", "silt", "phh2o", "soc", "bdod", "cfvo", "cec", "nitrogen"]

    def __init__(self, settings: Settings, cache, llm_service=None):
        self.settings = settings
        self.cache = cache
        self.llm = llm_service

    # ------------------------------------------------------------------
    # USDA Soil Texture Triangle classification
    # ------------------------------------------------------------------
    @staticmethod
    def _classify_texture(clay_pct: float, sand_pct: float, silt_pct: float) -> SoilType:
        """Classify soil texture using USDA texture triangle thresholds.
        All inputs are 0-100 percentages."""
        if clay_pct >= 40:
            if sand_pct >= 45:
                return SoilType.CLAYEY      # sandy clay
            if silt_pct >= 40:
                return SoilType.SILTY_CLAY
            return SoilType.CLAYEY
        if clay_pct >= 27:
            if sand_pct >= 20 and sand_pct <= 45:
                return SoilType.CLAY_LOAM
            if silt_pct >= 40:
                return SoilType.SILTY_CLAY
            return SoilType.CLAY_LOAM
        if silt_pct >= 50:
            if clay_pct >= 12:
                return SoilType.SILTY_LOAM
            return SoilType.SILTY_LOAM
        if sand_pct >= 70:
            if clay_pct >= 10:
                return SoilType.SANDY_LOAM
            return SoilType.SANDY
        if sand_pct >= 52:
            return SoilType.SANDY_LOAM
        return SoilType.LOAMY

    # ------------------------------------------------------------------
    # Drainage estimation from texture + bulk density
    # ------------------------------------------------------------------
    @staticmethod
    def _estimate_drainage(clay_pct: float, sand_pct: float, bdod: float) -> DrainageType:
        """Estimate drainage class from clay/sand % and bulk density (cg/cm³).
        bdod from ISRIC is in cg/cm³ (divide by 100 for g/cm³)."""
        bd_gcm3 = bdod / 100.0 if bdod else 1.3
        if clay_pct >= 40 or bd_gcm3 >= 1.6:
            return DrainageType.POOR
        if clay_pct >= 27 or bd_gcm3 >= 1.45:
            return DrainageType.MODERATE
        if sand_pct >= 60:
            return DrainageType.WELL
        return DrainageType.GOOD

    # ------------------------------------------------------------------
    # Effective soil depth from coarse fragment volume across depth ranges
    # ------------------------------------------------------------------
    @classmethod
    def _estimate_depth_cm(cls, cfvo_by_depth: dict[str, float]) -> float:
        """Estimate effective rooting depth using coarse-fragment volume (cm³/dm³).
        When cfvo exceeds 250 cm³/dm³ (~25%), the layer is considered restrictive."""
        if not cfvo_by_depth:
            return 100.0  # sensible default
        depth_range_cm = [5, 15, 30, 60, 100, 200]
        for label, upper_cm in zip(cls.DEPTH_LABELS, depth_range_cm):
            cfvo_val = cfvo_by_depth.get(label)
            if cfvo_val is not None and cfvo_val > 250:
                return float(upper_cm)
        # No restrictive layer found — full profile depth
        return 200.0

    # ------------------------------------------------------------------
    # Main fetch
    # ------------------------------------------------------------------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_soil_data(
        self,
        latitude: float,
        longitude: float,
    ) -> SoilData:
        cached = await self.cache.get("soil", lat=latitude, lon=longitude)
        if cached:
            logger.info(f"Soil cache hit for ({latitude}, {longitude})")
            cached_data = cached.copy()
            cached_data["cached"] = True
            return SoilData(**cached_data)

        try:
            import json
            soil_data = None

            try:
                # Build URL with ALL depths and ALL key properties
                props_param = "&".join(f"property={p}" for p in self.ISRIC_PROPERTIES)
                depths_param = "&".join(f"depth={d}" for d in self.DEPTH_LABELS)
                url = (
                    f"https://rest.isric.org/soilgrids/v2.0/properties/query"
                    f"?lon={longitude}&lat={latitude}&{props_param}&{depths_param}&value=mean"
                )

                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(url, headers={"User-Agent": "KisanSetu/2.0"})
                    response.raise_for_status()
                    data = response.json()

                # Parse into {property_name: {depth_label: mean_value}}
                prop_depth_map: dict[str, dict[str, float]] = {}
                for layer in data.get("properties", {}).get("layers", []):
                    name = layer.get("name")
                    if not name:
                        continue
                    depth_dict: dict[str, float] = {}
                    for depth_entry in layer.get("depths", []):
                        label = depth_entry.get("label", "")
                        mean_val = depth_entry.get("values", {}).get("mean")
                        if mean_val is not None:
                            depth_dict[label] = mean_val
                    prop_depth_map[name] = depth_dict

                # --- Weighted average over agronomic root zone (0-60 cm) ---
                # Weights proportional to layer thickness within 0-60 cm
                root_zone_weights = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15, "30-60cm": 30}
                total_weight = sum(root_zone_weights.values())

                def weighted_avg(prop_name: str) -> float:
                    vals = prop_depth_map.get(prop_name, {})
                    if not vals:
                        return 0.0
                    s, w = 0.0, 0.0
                    for lbl, wt in root_zone_weights.items():
                        v = vals.get(lbl)
                        if v is not None:
                            s += v * wt
                            w += wt
                    return s / w if w else 0.0

                clay_gkg = weighted_avg("clay")   # g/kg
                sand_gkg = weighted_avg("sand")
                silt_gkg = weighted_avg("silt")

                # Convert g/kg → percentage
                clay_pct = clay_gkg / 10.0
                sand_pct = sand_gkg / 10.0
                silt_pct = silt_gkg / 10.0

                # Normalise to 100% in case of rounding
                total = clay_pct + sand_pct + silt_pct
                if total > 0:
                    clay_pct = clay_pct / total * 100
                    sand_pct = sand_pct / total * 100
                    silt_pct = silt_pct / total * 100

                if total == 0:
                    raise ValueError("ISRIC returned zero clay/sand/silt — no valid data")

                texture = self._classify_texture(clay_pct, sand_pct, silt_pct)

                # pH — ISRIC stores as pH×10
                ph_raw = weighted_avg("phh2o")
                ph_val = ph_raw / 10.0 if ph_raw else 7.0
                ph_lo = max(0, round(ph_val - 0.3, 1))
                ph_hi = round(ph_val + 0.3, 1)

                # Soil organic carbon — ISRIC stores in dg/kg (= g/kg / 10)
                soc_dgkg = weighted_avg("soc")
                soc_pct = soc_dgkg / 100.0  # → %
                if soc_pct < 0.4:
                    oc_level = "Low"
                elif soc_pct < 0.75:
                    oc_level = "Medium-Low"
                elif soc_pct < 1.5:
                    oc_level = "Medium"
                elif soc_pct < 2.5:
                    oc_level = "Medium-High"
                else:
                    oc_level = "High"

                # Bulk density (cg/cm³) for drainage
                bdod = weighted_avg("bdod")
                drainage = self._estimate_drainage(clay_pct, sand_pct, bdod)

                # Effective soil depth from coarse fragments across all depths
                cfvo_by_depth = prop_depth_map.get("cfvo", {})
                depth_cm = self._estimate_depth_cm(cfvo_by_depth)

                # CEC for land quality indication
                cec = weighted_avg("cec")

                soil_data = {
                    "soil_texture": texture,
                    "soil_depth_cm": depth_cm,
                    "soil_drainage": drainage,
                    "ph_range": f"{ph_lo}-{ph_hi}",
                    "organic_carbon": oc_level,
                    "land_use_class": "Agricultural",
                    "source": "isric_soilgrids",
                }
                logger.info(
                    f"ISRIC SoilGrids data for ({latitude}, {longitude}): "
                    f"texture={texture.value}, depth={depth_cm}cm, "
                    f"clay={clay_pct:.1f}%, sand={sand_pct:.1f}%, silt={silt_pct:.1f}%, "
                    f"pH={ph_val:.1f}, SOC={soc_pct:.2f}%, bdod={bdod:.0f}cg/cm³, "
                    f"drainage={drainage.value}"
                )

            except Exception as isric_e:
                logger.warning(f"ISRIC SoilGrids failed: {isric_e}. Falling back to LLM estimation.")

            # ---- LLM fallback ----
            if not soil_data:
                if not self.llm:
                    raise Exception("LLM Service not injected and ISRIC failed")

                from langchain_core.messages import HumanMessage, SystemMessage

                prompt = f"""
                You are a GIS and Agricultural Soil Expert.
                Based on the coordinates Latitude: {latitude}, Longitude: {longitude} (which is likely in India), estimate the agricultural soil characteristics for this specific region.
                Consider the regional soil types (e.g. Vertisols/black cotton soil in Deccan, Laterite in Western Ghats, Alluvial in Indo-Gangetic plains, Red soil in peninsular India).

                Return the data STRICTLY as a JSON object with the following keys exactly:
                - "soil_texture" (Must be exactly one of: "clayey", "loamy", "sandy", "alluvial", "sandy_loam", "clay_loam", "silty_clay", "silty_loam", "laterite")
                - "soil_depth_cm" (float, typically between 30.0 and 200.0)
                - "soil_drainage" (Must be exactly one of: "poor", "moderate", "good", "well")
                - "ph_range" (string, e.g., "7.5-8.5")
                - "organic_carbon" (string, one of: "Low", "Medium-Low", "Medium", "Medium-High", "High")
                - "land_use_class" (string, e.g., "Agricultural", "Forest", "Urban")
                """

                messages = [
                    SystemMessage(content="You are a geographic soil analysis API. Output only valid JSON."),
                    HumanMessage(content=prompt),
                ]

                response = await self.llm.invoke(messages, temperature=0.2)
                raw_content = response.strip()

                if raw_content.startswith("```json"):
                    raw_content = raw_content[7:-3].strip()
                elif raw_content.startswith("```"):
                    raw_content = raw_content[3:-3].strip()

                raw_soil_data = json.loads(raw_content)

                soil_data = {}
                try:
                    soil_data["soil_texture"] = SoilType(raw_soil_data.get("soil_texture", "loamy").lower())
                except ValueError:
                    soil_data["soil_texture"] = SoilType.LOAMY
                try:
                    soil_data["soil_drainage"] = DrainageType(raw_soil_data.get("soil_drainage", "moderate").lower())
                except ValueError:
                    soil_data["soil_drainage"] = DrainageType.MODERATE

                soil_data["soil_depth_cm"] = float(raw_soil_data.get("soil_depth_cm", 100.0))
                soil_data["ph_range"] = str(raw_soil_data.get("ph_range", "6.5-7.5"))
                soil_data["organic_carbon"] = str(raw_soil_data.get("organic_carbon", "Medium"))
                soil_data["land_use_class"] = str(raw_soil_data.get("land_use_class", "Agricultural"))
                soil_data["source"] = "llm_estimation"
                soil_data["is_estimated"] = True

            await self.cache.set(
                "soil",
                soil_data,
                ttl=self.settings.WEATHER_CACHE_TTL,
                lat=latitude,
                lon=longitude,
            )

            return SoilData(**soil_data)

        except Exception as e:
            logger.warning(f"GIS fetch failed, using estimated data: {e}")
            soil_data = {
                "soil_texture": SoilType.LOAMY,
                "soil_depth_cm": 100.0,
                "soil_drainage": DrainageType.MODERATE,
                "ph_range": "6.5-7.5",
                "organic_carbon": "Medium",
                "land_use_class": "Agricultural",
                "source": "fallback",
                "is_estimated": True,
            }
            return SoilData(**soil_data)


