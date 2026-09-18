"""
HUE AI Output Validators and Safety Filters
Enforces structured schema constraints and beauty-only safety boundaries.
"""

import re
from typing import Dict, Any, Tuple

# Sensitive medical and identity terms that must never be presented as diagnosis
FORBIDDEN_DIAGNOSTIC_TERMS = [
    r'\bacne\b', r'\brosacea\b', r'\beczema\b', r'\bpsoriasis\b',
    r'\bdermatitis\b', r'\bmelasma\b', r'\bhyperpigmentation\b',
    r'\bpathology\b', r'\bdisease\b', r'\binfection\b', r'\ballergy\b',
    r'\ballergic\b', r'\blesion\b', r'\bcancer\b', r'\btumor\b',
    r'\brace\b', r'\bethnicity\b', r'\bnationality\b', r'\breligion\b',
    r'\bcaucasian\b', r'\bhispanic\b', r'\blatino\b', r'\basian\b',
    r'\bblack person\b', r'\bwhite person\b'
]


def sanitize_beauty_text(text: str) -> str:
    """Strip or soften any diagnostic / identity claims from AI output."""
    if not isinstance(text, str):
        return str(text or '')

    sanitized = text
    for pattern in FORBIDDEN_DIAGNOSTIC_TERMS:
        sanitized = re.sub(pattern, 'complexion variation', sanitized, flags=re.IGNORECASE)
    return sanitized


def validate_color_dict(color: Any, default_name: str = "Neutral Rose", default_hex: str = "#C48D7F") -> Dict[str, str]:
    """Ensure a color dictionary adheres to normalized color structure."""
    if not isinstance(color, dict):
        return {
            "color_name": default_name,
            "hex": default_hex,
            "temperature": "neutral",
            "saturation": "medium",
            "brightness": "medium"
        }

    hex_val = str(color.get("hex", default_hex)).strip()
    if not re.match(r'^#[0-9a-fA-F]{6}$', hex_val):
        hex_val = default_hex

    return {
        "color_name": str(color.get("color_name") or default_name),
        "hex": hex_val,
        "temperature": str(color.get("temperature") or "neutral"),
        "saturation": str(color.get("saturation") or "medium"),
        "brightness": str(color.get("brightness") or "medium")
    }


def validate_confidence(conf_data: Any) -> Dict[str, float]:
    """Ensure confidence values are properly bounded between 0.0 and 1.0."""
    if not isinstance(conf_data, dict):
        conf_data = {"overall": float(conf_data or 0.85)}

    def bound(val, default=0.85):
        try:
            f = float(val)
            return max(0.0, min(1.0, round(f, 2)))
        except (ValueError, TypeError):
            return default

    return {
        "overall": bound(conf_data.get("overall"), 0.88),
        "outfit_color_analysis": bound(conf_data.get("outfit_color_analysis"), 0.90),
        "makeup_color_recommendation": bound(conf_data.get("makeup_color_recommendation"), 0.86),
    }


def validate_makeup_response(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
    """Validate and sanitize full makeup styling response."""
    if not isinstance(data, dict):
        return False, {}, "Response is not a valid dictionary"

    cleaned = {}
    cleaned["look_name"] = sanitize_beauty_text(data.get("look_name", "Curated Beauty Direction"))
    cleaned["summary"] = sanitize_beauty_text(data.get("summary", "Personalized makeup look designed to balance visual contrast and complement your natural features."))
    cleaned["confidence"] = validate_confidence(data.get("confidence", {}))
    cleaned["face_analysis"] = data.get("face_analysis") or {}
    cleaned["outfit_analysis"] = data.get("outfit_analysis") or {}

    raw_recs = data.get("recommendations", {})
    if not isinstance(raw_recs, dict):
        raw_recs = {}

    cleaned_recs = {}
    required_cats = ["base", "blush", "bronzer", "highlighter", "eyeshadow", "eyeliner", "mascara", "brows", "lips"]
    for cat in required_cats:
        rec = raw_recs.get(cat, {})
        if not isinstance(rec, dict):
            rec = {}
        cleaned_recs[cat] = {
            "product_direction": sanitize_beauty_text(rec.get("product_direction", f"Tailored {cat} approach")),
            "color": validate_color_dict(rec.get("color")),
            "intensity": str(rec.get("intensity", "medium")),
            "finish": str(rec.get("finish", "natural")),
            "placement": sanitize_beauty_text(rec.get("placement", "Standard balanced application")),
            "reasoning": sanitize_beauty_text(rec.get("reasoning", "Harmonizes with facial features and styling")),
            "extra_details": rec.get("extra_details", {})
        }

    cleaned["recommendations"] = cleaned_recs

    raw_steps = data.get("application_steps", [])
    if not isinstance(raw_steps, list) or len(raw_steps) == 0:
        raw_steps = [
            {"step_number": 1, "category": "Base", "title": "Foundation & Prep", "guidance": "Apply sheer to medium coverage evenly from the center of face outward."},
            {"step_number": 2, "category": "Concealer", "title": "Targeted Concealer", "guidance": "Brighten under-eyes and spot-conceal only where needed."},
            {"step_number": 3, "category": "Bronzer", "title": "Warmth & Dimension", "guidance": "Sweep lightly along the perimeter of the forehead and high cheekbones."},
            {"step_number": 4, "category": "Blush", "title": "Healthy Flush", "guidance": "Pat onto the apples of cheeks and blend back toward temples."},
            {"step_number": 5, "category": "Eyes", "title": "Eyeshadow Wash", "guidance": "Wash the primary neutral shade across lid, softly defining crease."},
            {"step_number": 6, "category": "Liner", "title": "Lashline Definition", "guidance": "Tightline upper lash base for natural depth."},
            {"step_number": 7, "category": "Mascara", "title": "Lash Lift", "guidance": "Wiggle at the roots and brush up for separated length."},
            {"step_number": 8, "category": "Brows", "title": "Soft Brow Architecture", "guidance": "Brush up with clear or tinted gel, filling sparse gaps with fine strokes."},
            {"step_number": 9, "category": "Lips", "title": "Lip Tone & Definition", "guidance": "Line softly and apply complementary lip color."},
            {"step_number": 10, "category": "Final Touch", "title": "Setting & Radiance", "guidance": "Light dusting of translucent powder in T-zone, followed by setting mist."}
        ]

    cleaned_steps = []
    for i, step in enumerate(raw_steps, 1):
        if not isinstance(step, dict):
            continue
        cleaned_steps.append({
            "step_number": step.get("step_number", i),
            "category": str(step.get("category", "Step")),
            "title": sanitize_beauty_text(step.get("title", f"Step {i}")),
            "product_direction": sanitize_beauty_text(step.get("product_direction", "")),
            "shade_direction": sanitize_beauty_text(step.get("shade_direction", "")),
            "color": validate_color_dict(step.get("color")),
            "intensity": str(step.get("intensity", "medium")),
            "guidance": sanitize_beauty_text(step.get("guidance", "")),
            "reasoning": sanitize_beauty_text(step.get("reasoning", ""))
        })

    cleaned["application_steps"] = cleaned_steps
    cleaned["notes"] = [sanitize_beauty_text(n) for n in data.get("notes", []) if isinstance(n, str)]

    return True, cleaned, ""
