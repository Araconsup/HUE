"""
HUE AI JSON Schemas
Structured contracts for AI Gateway outputs and server-side validation.
"""

NORMALIZED_COLOR_SCHEMA = {
    "type": "object",
    "properties": {
        "color_name": {"type": "string"},
        "hex": {"type": "string"},
        "temperature": {"type": "string", "enum": ["warm", "cool", "neutral", "neutral-warm", "neutral-cool"]},
        "saturation": {"type": "string", "enum": ["low", "medium", "high", "muted", "vibrant"]},
        "brightness": {"type": "string", "enum": ["light", "medium", "deep", "soft", "rich"]}
    },
    "required": ["color_name", "hex", "temperature"]
}

IMAGE_VALIDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "is_usable": {"type": "boolean"},
        "face_detected": {"type": "boolean"},
        "outfit_detected": {"type": "boolean"},
        "lighting_quality": {"type": "string", "enum": ["adequate", "too_dark", "too_bright", "harsh_shadows"]},
        "sharpness_quality": {"type": "string", "enum": ["sharp", "acceptable", "blurry"]},
        "obstruction_detected": {"type": "boolean"},
        "rejection_reason": {"type": ["string", "null"]},
        "user_guidance": {"type": "string"}
    },
    "required": ["is_usable", "face_detected", "lighting_quality", "sharpness_quality", "user_guidance"]
}

FACE_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "image_quality": {
            "type": "object",
            "properties": {
                "lighting": {"type": "string"},
                "sharpness": {"type": "string"},
                "clarity_rating": {"type": "number"}
            }
        },
        "face_visibility": {
            "type": "object",
            "properties": {
                "unobstructed": {"type": "boolean"},
                "eyes_visible": {"type": "boolean"},
                "lips_visible": {"type": "boolean"},
                "brows_visible": {"type": "boolean"}
            }
        },
        "complexion_observations": {
            "type": "object",
            "properties": {
                "visible_finish": {"type": "string"},
                "apparent_depth": {"type": "string"},
                "observation_notes": {"type": "string"}
            }
        },
        "visible_undertone_indicators": {
            "type": "object",
            "properties": {
                "apparent_undertone": {"type": "string", "enum": ["warm", "cool", "neutral", "olive", "neutral-warm", "neutral-cool"]},
                "confidence": {"type": "number"},
                "visual_markers": {"type": "string"}
            }
        },
        "face_shape_estimate": {
            "type": "object",
            "properties": {
                "shape": {"type": "string"},
                "contour_focus_area": {"type": "string"}
            }
        },
        "eye_area": {
            "type": "object",
            "properties": {
                "apparent_shape": {"type": "string"},
                "lid_space": {"type": "string"},
                "recommended_focus": {"type": "string"}
            }
        },
        "lip_area": {
            "type": "object",
            "properties": {
                "apparent_fullness": {"type": "string"},
                "natural_tint_depth": {"type": "string"}
            }
        },
        "brow_area": {
            "type": "object",
            "properties": {
                "density": {"type": "string"},
                "shape_direction": {"type": "string"}
            }
        },
        "existing_makeup": {
            "type": "object",
            "properties": {
                "detected": {"type": "boolean"},
                "description": {"type": "string"}
            }
        },
        "color_harmony": {
            "type": "object",
            "properties": {
                "flattering_families": {"type": "array", "items": {"type": "string"}},
                "contrast_level": {"type": "string"}
            }
        },
        "recommended_makeup_direction": {
            "type": "object",
            "properties": {
                "concept": {"type": "string"},
                "palette_vibe": {"type": "string"}
            }
        }
    },
    "required": ["complexion_observations", "visible_undertone_indicators", "recommended_makeup_direction"]
}

OUTFIT_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "dominant_colors": {"type": "array", "items": NORMALIZED_COLOR_SCHEMA},
        "secondary_colors": {"type": "array", "items": NORMALIZED_COLOR_SCHEMA},
        "pattern": {"type": "string"},
        "contrast": {"type": "string"},
        "temperature": {"type": "string"},
        "saturation": {"type": "string"},
        "brightness": {"type": "string"},
        "style": {"type": "string"},
        "formality": {"type": "string"},
        "overall_aesthetic": {"type": "string"},
        "styling_notes": {"type": "string"}
    },
    "required": ["dominant_colors", "temperature", "style", "formality", "overall_aesthetic"]
}

MAKEUP_LOOK_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "look_name": {"type": "string"},
        "summary": {"type": "string"},
        "confidence": {
            "type": "object",
            "properties": {
                "overall": {"type": "number"},
                "outfit_color_analysis": {"type": "number"},
                "makeup_color_recommendation": {"type": "number"}
            },
            "required": ["overall"]
        },
        "face_analysis": {"type": "object"},
        "outfit_analysis": {"type": "object"},
        "recommendations": {
            "type": "object",
            "properties": {
                "base": {"type": "object"},
                "blush": {"type": "object"},
                "bronzer": {"type": "object"},
                "highlighter": {"type": "object"},
                "eyeshadow": {"type": "object"},
                "eyeliner": {"type": "object"},
                "mascara": {"type": "object"},
                "brows": {"type": "object"},
                "lips": {"type": "object"}
            },
            "required": ["base", "blush", "eyeshadow", "lips"]
        },
        "application_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step_number": {"type": "integer"},
                    "category": {"type": "string"},
                    "title": {"type": "string"},
                    "product_direction": {"type": "string"},
                    "shade_direction": {"type": "string"},
                    "color": NORMALIZED_COLOR_SCHEMA,
                    "intensity": {"type": "string"},
                    "guidance": {"type": "string"},
                    "reasoning": {"type": "string"}
                },
                "required": ["step_number", "category", "title", "guidance"]
            }
        },
        "notes": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["look_name", "summary", "confidence", "recommendations", "application_steps"]
}
