import json
import logging
from typing import Dict, List, Any, Optional

from core.logging import get_logger

logger = get_logger(__name__)

# In-memory crop disease / treatment knowledge base
# Production: replace with vector DB + embeddings
CROP_DISEASE_KNOWLEDGE = [
    {
        "crop": "wheat",
        "disease": "Yellow Rust (Stripe Rust)",
        "symptoms": "Yellow-orange pustules in stripes on leaves",
        "treatment": "Apply fungicide containing Propiconazole or Tebuconazole. Remove infected leaves.",
        "organic": "Spray neem oil extract (3%) every 10 days.",
        "fertilizer": "Apply balanced NPK (10:26:26) after recovery.",
        "preventive": "Use resistant varieties like HD-2967. Avoid late sowing.",
    },
    {
        "crop": "wheat",
        "disease": "Brown Rust (Leaf Rust)",
        "symptoms": "Brown circular pustules on leaf surface",
        "treatment": "Apply Mancozeb or Zineb fungicide at first sign.",
        "organic": "Baking soda spray (1 tbsp per liter water).",
        "fertilizer": "Apply zinc sulfate 25 kg/ha.",
        "preventive": "Early sowing and crop rotation with legumes.",
    },
    {
        "crop": "rice",
        "disease": "Blast (Rice Blast)",
        "symptoms": "Diamond-shaped lesions with gray centers on leaves and neck",
        "treatment": "Spray Tricyclazole 75% WP (0.1%) or Isoprothiolane.",
        "organic": "Spray cow urine (10%) or Pseudomonas fluorescens.",
        "fertilizer": "Reduce nitrogen, apply potash 50 kg/ha.",
        "preventive": "Avoid excess nitrogen. Maintain 2-3 cm water level.",
    },
    {
        "crop": "rice",
        "disease": "Bacterial Leaf Blight",
        "symptoms": "Water-soaked lesions turning yellow-white along leaf margins",
        "treatment": "Spray Streptocycline 100 ppm + Copper oxychloride 0.25%.",
        "organic": "Spray garlic-chili extract (5%).",
        "fertilizer": "Avoid excessive nitrogen. Use balanced NPK.",
        "preventive": "Use resistant varieties. Drain field periodically.",
    },
    {
        "crop": "cotton",
        "disease": "Bollworm",
        "symptoms": "Holes in bolls, dropping flowers, larvae inside squares",
        "treatment": "Apply Chlorantraniliprole 18.5% SC (0.015%) or Spinosad.",
        "organic": "Release Trichogramma parasitoids. Use pheromone traps.",
        "fertilizer": "Apply calcium nitrate during boll formation.",
        "preventive": "Grow trap crops like marigold on borders. Monitor eggs.",
    },
    {
        "crop": "cotton",
        "disease": "Leaf Curl Virus",
        "symptoms": "Upward curling of leaves, stunted growth, vein thickening",
        "treatment": "No chemical cure. Remove and burn infected plants.",
        "organic": "Control whitefly vector with neem oil (5%).",
        "fertilizer": "Apply micronutrient mixture (Zn, Fe, B).",
        "preventive": "Use resistant varieties like RCH-308. Avoid ratoon cotton.",
    },
    {
        "crop": "sugarcane",
        "disease": "Red Rot",
        "symptoms": "Reddish internal tissues with white patches, bad odor",
        "treatment": "Dip setts in Carbendazim 0.1% before planting.",
        "organic": "Hot water treatment of setts at 52°C for 30 min.",
        "fertilizer": "Apply Trichoderma viride @ 10 g/sett.",
        "preventive": "Use disease-free setts. Avoid waterlogging.",
    },
    {
        "crop": "sugarcane",
        "disease": "Smut",
        "symptoms": "Whip-like black structures emerging from leaf whorl",
        "treatment": "Remove and burn smut whips before spore release.",
        "organic": "Soak setts in cow dung slurry for 24 hours before planting.",
        "fertilizer": "Apply neem cake 500 kg/ha at planting.",
        "preventive": "Use resistant varieties. Rogue out infected plants.",
    },
    {
        "crop": "tomato",
        "disease": "Early Blight",
        "symptoms": "Concentric rings on lower leaves, yellowing, defoliation",
        "treatment": "Apply Mancozeb 75% WP (0.2%) or Chlorothalonil.",
        "organic": "Spray copper oxychloride (0.3%) or Bordeaux mixture.",
        "fertilizer": "Apply calcium ammonium nitrate (CAN) 100 kg/ha.",
        "preventive": "Mulch to reduce soil splash. Stake plants.",
    },
    {
        "crop": "tomato",
        "disease": "Late Blight",
        "symptoms": "Water-soaked lesions on leaves/stems, white fungal growth on underside",
        "treatment": "Apply Metalaxyl + Mancozeb (Ridomil Gold) at 0.2%.",
        "organic": "Spray compost tea or milk solution (1:10).",
        "fertilizer": "Avoid late nitrogen. Apply potash.",
        "preventive": "Ensure good ventilation. Avoid overhead irrigation.",
    },
    {
        "crop": "potato",
        "disease": "Late Blight",
        "symptoms": "Brown-black lesions on leaves, white mold on underside in humid weather",
        "treatment": "Apply Mancozeb 75% WP (0.2%) or Metalaxyl-M 4% + Mancozeb 64% WP.",
        "organic": "Spray with horsetail tea or copper-based organic fungicide.",
        "fertilizer": "Apply muriate of potash at earthing-up stage.",
        "preventive": "Haulm destruction 15 days before harvest. Use certified seed.",
    },
    {
        "crop": "maize",
        "disease": "Fall Armyworm",
        "symptoms": "Window-pane holes in leaves, frass in whorl, dead heart",
        "treatment": "Apply Chlorantraniliprole 18.5% SC or Emamectin benzoate.",
        "organic": "Apply Beauveria bassiana or Metarhizium anisopliae.",
        "fertilizer": "Apply micronutrient spray (Zn, B, Mg).",
        "preventive": "Intercrop with legumes. Use pheromone traps for monitoring.",
    },
    {
        "crop": "groundnut",
        "disease": "Tikka Leaf Spot",
        "symptoms": "Circular dark brown spots with yellow halos on leaflets",
        "treatment": "Spray Chlorothalonil 75% WP (0.2%) or Propiconazole.",
        "organic": "Spray neem seed kernel extract (5%).",
        "fertilizer": "Apply gypsum 500 kg/ha at pegging stage.",
        "preventive": "Use resistant varieties like ICGV-91114. Deep ploughing.",
    },
    {
        "crop": "soybean",
        "disease": "Yellow Mosaic Virus",
        "symptoms": "Yellow mosaic pattern on leaves, stunted plants, reduced podding",
        "treatment": "No chemical cure. Roguing and vector control.",
        "organic": "Control whitefly with yellow sticky traps and neem oil.",
        "fertilizer": "Apply Rhizobium + PSB seed treatment.",
        "preventive": "Use resistant varieties like JS-335. Early sowing.",
    },
    {
        "crop": "brinjal",
        "disease": "Fruit and Shoot Borer",
        "symptoms": "Wilting shoot tips, holes in fruits with frass",
        "treatment": "Apply Emamectin benzoate 5% SG or Spinosad 45% SC.",
        "organic": "Release Trichogramma chilonis @ 1 lakh/ha.",
        "fertilizer": "Apply boron 10 kg/ha during flowering.",
        "preventive": "Clip damaged shoots. Use nylon net barriers.",
    },
    {
        "crop": "chickpea",
        "disease": "Ascochyta Blight",
        "symptoms": "Brown lesions on stems, leaves and pods with pycnidia",
        "treatment": "Spray Mancozeb 75% WP (0.2%) or Carbendazim.",
        "organic": "Spray Trichoderma harzianum (0.4%).",
        "fertilizer": "Apply Rhizobium + PSB at sowing.",
        "preventive": "Use certified seed. Treat seed with Thiram.",
    },
]

# Market price estimates (₹ per quintal, seasonal averages)
MARKET_PRICES = {
    "wheat": "2,400 - 2,800",
    "rice": "2,100 - 2,500",
    "cotton": "6,500 - 7,200",
    "sugarcane": "340 - 380 (per ton)",
    "tomato": "2,000 - 3,500",
    "potato": "1,800 - 2,400",
    "maize": "2,200 - 2,600",
    "groundnut": "6,000 - 6,800",
    "soybean": "4,200 - 4,800",
    "brinjal": "1,800 - 2,800",
    "chickpea": "5,500 - 6,200",
    "mustard": "5,800 - 6,400",
    "onion": "2,200 - 3,000",
    "garlic": "8,000 - 10,000",
}

# Harvest window estimates (weeks from current growth stage)
HARVEST_ESTIMATES = {
    "wheat": "8-12 weeks (Rabi harvest)",
    "rice": "4-6 weeks (if in grain filling)",
    "cotton": "6-10 weeks (boll opening stage)",
    "sugarcane": "12-18 months total (check maturity)",
    "tomato": "2-4 weeks (fruit ripening)",
    "potato": "3-5 weeks (tuber bulking)",
    "maize": "4-8 weeks (grain filling/dent stage)",
    "groundnut": "3-6 weeks (peg maturation)",
    "soybean": "4-6 weeks (pod filling)",
    "brinjal": "2-3 weeks (continuous harvest)",
    "chickpea": "6-10 weeks (pod development)",
    "mustard": "6-8 weeks (siliqua formation)",
    "onion": "3-4 weeks (bulb maturity)",
    "garlic": "4-6 weeks (clove formation)",
}


class CropKnowledgeBase:
    """
    Simple RAG-style retrieval for crop disease treatment knowledge.
    Production: replace with vector DB + embedding search.
    """

    def __init__(self):
        self.knowledge = CROP_DISEASE_KNOWLEDGE

    def retrieve(self, crop: Optional[str], disease_hint: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant knowledge entries by crop name and optional disease hint."""
        crop_lower = (crop or "").lower().strip()
        hint_lower = (disease_hint or "").lower().strip()

        results = []
        for entry in self.knowledge:
            match_crop = crop_lower in entry["crop"] or entry["crop"] in crop_lower
            match_hint = not hint_lower or hint_lower in entry["disease"].lower()
            if match_crop or match_hint:
                results.append(entry)

        if not results and hint_lower:
            # Fallback: fuzzy search on symptoms
            for entry in self.knowledge:
                if hint_lower in entry["symptoms"].lower() or hint_lower in entry["disease"].lower():
                    results.append(entry)

        return results[:3]

    def get_price(self, crop: Optional[str]) -> str:
        if not crop:
            return "—"
        return MARKET_PRICES.get(crop.lower().strip(), "Market price varies by mandi")

    def get_harvest(self, crop: Optional[str]) -> str:
        if not crop:
            return "—"
        return HARVEST_ESTIMATES.get(crop.lower().strip(), "Check with local KVK")

    def list_crops(self) -> List[str]:
        return sorted({e["crop"] for e in self.knowledge})
