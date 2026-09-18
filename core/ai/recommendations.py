"""
HUE Recommendation Engine
Converts visual observations into tailored makeup categories, ordered 10-step routines, and normalized colors.
"""

import logging
from typing import Dict, Any, List
from .client import AIClient
from .prompts import BASE_VISION_SYSTEM_PROMPT, MAKEUP_RECOMMENDATION_PROMPT
from .validators import validate_makeup_response, sanitize_beauty_text

logger = logging.getLogger('hue.ai.recommendations')


class RecommendationEngine:
    """
    Translates visual analysis into structured cosmetic recommendations and application routines.
    """

    def __init__(self, client: AIClient = None):
        self.client = client or AIClient()

    def generate_recommendations(
        self,
        mode: str,
        face_analysis: Dict[str, Any] = None,
        outfit_analysis: Dict[str, Any] = None,
        combined_data: Dict[str, Any] = None,
        image_data_uris: List[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes recommendations from the visual analysis.
        Returns a validated dictionary matching MAKEUP_LOOK_RESPONSE_SCHEMA.
        """
        # If the vision analysis call already produced the complete recommendation structure:
        raw_source = combined_data or face_analysis or outfit_analysis or {}
        if "recommendations" in raw_source and "application_steps" in raw_source:
            valid, cleaned, err = validate_makeup_response(raw_source)
            if valid:
                return cleaned

        # Otherwise, query the AI gateway with the observed context to generate recommendations
        context_summary = []
        if face_analysis:
            undertone = face_analysis.get("visible_undertone_indicators", {}).get("apparent_undertone", "neutral")
            shape = face_analysis.get("face_shape_estimate", {}).get("shape", "balanced")
            context_summary.append(f"Face features: undertone={undertone}, shape={shape}")

        if outfit_analysis:
            dominant = [c.get("color_name") for c in outfit_analysis.get("dominant_colors", []) if isinstance(c, dict)]
            aesthetic = outfit_analysis.get("overall_aesthetic", "Contemporary")
            context_summary.append(f"Outfit features: colors={', '.join(dominant)}, aesthetic={aesthetic}")

        prompt = (
            f"{MAKEUP_RECOMMENDATION_PROMPT}\n\n"
            f"Visual Observations Context:\n"
            f"{' | '.join(context_summary)}"
        )

        try:
            if image_data_uris:
                response = self.client.complete_vision(prompt, image_data_uris, BASE_VISION_SYSTEM_PROMPT)
            else:
                response = self.client.complete_text(prompt, BASE_VISION_SYSTEM_PROMPT)

            # Ensure face and outfit analyses are preserved in the response
            if face_analysis and "face_analysis" not in response:
                response["face_analysis"] = face_analysis
            if outfit_analysis and "outfit_analysis" not in response:
                response["outfit_analysis"] = outfit_analysis

            valid, cleaned, err = validate_makeup_response(response)
            if valid:
                return cleaned
            else:
                logger.warning(f"Recommendation validation warning: {err}, falling back to safe defaults")
                valid, fallback, _ = validate_makeup_response({})
                return fallback
        except Exception as e:
            logger.exception("Error generating recommendations")
            valid, fallback, _ = validate_makeup_response({})
            return fallback
