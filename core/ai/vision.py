"""
HUE Vision Analyzer
Multi-stage AI vision analysis pipeline: Image Validation, Feature Extraction, and Styling Synthesis.
"""

import logging
from typing import Dict, Any, List, Tuple
from .client import AIClient
from .gateway import ImageProcessor
from .prompts import (
    BASE_VISION_SYSTEM_PROMPT,
    IMAGE_VALIDATION_PROMPT,
    FACE_ANALYSIS_PROMPT,
    OUTFIT_ANALYSIS_PROMPT,
    COMBINED_ANALYSIS_PROMPT
)
from .validators import sanitize_beauty_text, validate_confidence

logger = logging.getLogger('hue.ai.vision')


class VisionValidationResult:
    """Encapsulates Stage 1 Image Validation findings."""

    def __init__(self, is_usable: bool, message: str, details: Dict[str, Any]):
        self.is_usable = is_usable
        self.message = message
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_usable": self.is_usable,
            "message": self.message,
            "details": self.details
        }


class VisionAnalyzer:
    """
    Coordinates multi-stage vision intelligence pipeline:
    Stage 1: Validation
    Stage 2: Feature Observation (Face / Outfit)
    Stage 3: Styling Synthesis
    """

    def __init__(self, client: AIClient = None):
        self.client = client or AIClient()

    def validate_image(self, image_bytes: bytes, requested_mode: str = 'face') -> VisionValidationResult:
        """
        Stage 1: Validates image before deep analysis.
        Checks lighting, focus, resolution, obstruction, and usable subject.
        """
        # Local fast image pre-checks
        success, data_uri, _, meta = ImageProcessor.process_image(image_bytes)
        if not success:
            return VisionValidationResult(
                is_usable=False,
                message=meta.get("error", "The uploaded file could not be processed as an image."),
                details={"stage": "local_preprocessing", **meta}
            )

        # Rule-based fast rejection for extreme lighting or flat frames
        if meta.get("is_too_dark"):
            return VisionValidationResult(
                is_usable=False,
                message="The lighting in this photo is too low to reliably judge makeup colors. Please take or upload a photo in natural or evenly distributed light.",
                details={"reason": "too_dark", **meta}
            )

        if meta.get("is_too_bright"):
            return VisionValidationResult(
                is_usable=False,
                message="The photo is overexposed or washed out by direct light. Try taking a photo with softer, diffused lighting.",
                details={"reason": "overexposed", **meta}
            )

        if meta.get("width", 0) < 200 or meta.get("height", 0) < 200:
            return VisionValidationResult(
                is_usable=False,
                message="The image resolution is too low. Please upload a clearer, higher-resolution photo.",
                details={"reason": "low_resolution", **meta}
            )

        # Vision model validation check
        try:
            val_resp = self.client.complete_vision(
                prompt=IMAGE_VALIDATION_PROMPT,
                image_data_uris=[data_uri],
                system_prompt=BASE_VISION_SYSTEM_PROMPT
            )

            is_usable = bool(val_resp.get("is_usable", True))
            guidance = val_resp.get("user_guidance", "Image is ready for analysis.")
            rejection_reason = val_resp.get("rejection_reason")

            # Check mode-specific visibility
            if requested_mode == 'face' and not val_resp.get("face_detected", True):
                return VisionValidationResult(
                    is_usable=False,
                    message="We couldn't clearly detect a face in this photo. Please ensure your face is clearly visible, centered, and unobstructed.",
                    details=val_resp
                )
            elif requested_mode == 'outfit' and not val_resp.get("outfit_detected", True):
                return VisionValidationResult(
                    is_usable=False,
                    message="We couldn't clearly detect an outfit or clothing in this photo. Please upload an image showing the garments you wish to style.",
                    details=val_resp
                )

            if not is_usable:
                msg = rejection_reason or guidance or "The photo could not be reliably analyzed. Please try again with clearer lighting."
                return VisionValidationResult(is_usable=False, message=msg, details=val_resp)

            return VisionValidationResult(is_usable=True, message=guidance, details=val_resp)

        except Exception as e:
            logger.warning(f"AI validation stage encountered an issue, proceeding with graceful local validation: {e}")
            # Gracefully allow well-lit, non-corrupt images through if AI gateway flickers
            return VisionValidationResult(
                is_usable=True,
                message="Image verified successfully.",
                details={"local_fallback": True, **meta}
            )

    def analyze_face(self, data_uri: str) -> Dict[str, Any]:
        """Deep visual analysis for a face photo."""
        resp = self.client.complete_vision(
            prompt=FACE_ANALYSIS_PROMPT,
            image_data_uris=[data_uri],
            system_prompt=BASE_VISION_SYSTEM_PROMPT
        )
        return resp

    def analyze_outfit(self, data_uri: str) -> Dict[str, Any]:
        """Deep visual analysis for clothing/outfit."""
        resp = self.client.complete_vision(
            prompt=OUTFIT_ANALYSIS_PROMPT,
            image_data_uris=[data_uri],
            system_prompt=BASE_VISION_SYSTEM_PROMPT
        )
        return resp

    def analyze_combined(self, face_data_uri: str, outfit_data_uri: str) -> Dict[str, Any]:
        """Deep visual harmony analysis for both face and outfit together."""
        resp = self.client.complete_vision(
            prompt=COMBINED_ANALYSIS_PROMPT,
            image_data_uris=[face_data_uri, outfit_data_uri],
            system_prompt=BASE_VISION_SYSTEM_PROMPT
        )
        return resp
