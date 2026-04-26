import json
import logging
import re
from typing import Dict, Any, Tuple, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage

from core.logging import get_logger

logger = get_logger(__name__)


class HybridEligibilityEngine:
    """
    Evaluates farmer eligibility using a deterministic forward-chaining rule
    evaluation, falling back to an LLM for fuzzy logic resolution.
    """

    def __init__(self, llm_service=None):
        self.llm = llm_service

    def _evaluate_deterministic_rules(
        self,
        user_data: Dict[str, Any],
        scheme_rules: Dict[str, Any],
    ) -> Tuple[bool, bool, List[str], str, float]:
        """
        Evaluates hard business logic based on defined JSON schemas.
        Returns: (handled_by_rules, is_eligible, missing_fields, reason, confidence_score)
        """
        missing_fields = []
        required_fields = scheme_rules.get("required_fields", [])

        # 1. Verification of Required Fields
        for field in required_fields:
            if field not in user_data or user_data[field] in [None, "", "unknown"]:
                missing_fields.append(field)

        if missing_fields:
            return (
                True,
                False,
                missing_fields,
                f"Missing required fields: {', '.join(missing_fields)}",
                1.0,
            )

        # 2. Numeric Threshold Evaluation (e.g., Land Size)
        max_land = scheme_rules.get("eligibility_criteria", {}).get(
            "max_land_size_hectares"
        )
        if max_land and "land_area" in user_data:
            try:
                user_land = float(user_data["land_area"])
                if user_land > max_land:
                    return (
                        True,
                        False,
                        [],
                        f"Land size {user_land} ha exceeds limit of {max_land} ha.",
                        1.0,
                    )
            except (ValueError, TypeError):
                # Value is fuzzy (e.g., "around 2 acres"). Hand control to LLM fallback.
                return False, False, [], "", 0.0

        # 3. Categorical Exclusions (e.g., Pensioners, Institutional Landholders)
        exclusions = scheme_rules.get("eligibility_criteria", {}).get("exclusions", [])
        user_category = user_data.get("farmer_category", "")
        if user_category and user_category in exclusions:
            return (
                True,
                False,
                [],
                f"Ineligible: User falls under exclusion category '{user_category}'.",
                1.0,
            )

        # 4. Aadhaar format validation (12 digits)
        aadhaar = user_data.get("aadhaar_number", "")
        if aadhaar and not re.match(r"^\d{12}$", str(aadhaar)):
            return (
                True,
                False,
                [],
                "Invalid Aadhaar number format. Must be 12 digits.",
                1.0,
            )

        # If data is perfectly structured and clears all hurdles
        return True, True, [], "User meets all deterministic criteria.", 1.0

    async def _evaluate_llm_fallback(
        self,
        user_data: Dict[str, Any],
        scheme_rules: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Uses an LLM to interpret fuzzy conditions, acting as the cognitive fallback.
        """
        if not self.llm:
            return {
                "eligible": False,
                "missing_fields": [],
                "reason": "LLM service unavailable for fuzzy evaluation.",
                "confidence_score": 0.0,
            }

        system_msg = SystemMessage(
            content="You are an expert government compliance officer evaluating agricultural scheme eligibility."
        )
        user_msg = HumanMessage(
            content=f"""Evaluate the following User Data against the Scheme Rules.
Convert fuzzy regional measurements (like acres or bighas) to hectares if necessary to evaluate rules.
1 Hectare = 2.47 Acres.

Scheme Rules: {json.dumps(scheme_rules)}
User Data: {json.dumps(user_data)}

Provide a confidence score between 0.0 and 1.0 based on how clear the user's data is.
Return ONLY a valid JSON object matching this exact schema:
{{
    "eligible": boolean,
    "missing_fields": ["array", "of", "missing", "keys"],
    "reason": "Detailed explanation of the decision",
    "confidence_score": float
}}"""
        )

        try:
            response = await self.llm.invoke([system_msg, user_msg], temperature=0)
            raw_json = response.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw_json)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"LLM generated invalid JSON: {e}")
            return {
                "eligible": False,
                "missing_fields": [],
                "reason": "System error during semantic eligibility parsing.",
                "confidence_score": 0.0,
            }
        except Exception as e:
            logger.error(f"LLM fallback failed: {e}")
            return {
                "eligible": False,
                "missing_fields": [],
                "reason": f"LLM evaluation error: {str(e)}",
                "confidence_score": 0.0,
            }

    async def check_eligibility(
        self,
        user_data: Dict[str, Any],
        scheme_rules: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Main entry point for the hybrid engine."""
        handled, eligible, missing, reason, confidence = (
            self._evaluate_deterministic_rules(user_data, scheme_rules)
        )

        if handled:
            logger.info(
                "Eligibility conclusively handled by deterministic rule engine."
            )
            return {
                "eligible": eligible,
                "missing_fields": missing,
                "reason": reason,
                "confidence_score": confidence,
            }

        logger.info("Fuzzy data detected. Falling back to LLM semantic evaluation.")
        return await self._evaluate_llm_fallback(user_data, scheme_rules)
