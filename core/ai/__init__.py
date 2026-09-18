"""
HUE AI Intelligence Module
Provider-independent AI architecture for vision analysis, styling, and product matching.
"""

from .client import AIClient
from .vision import VisionAnalyzer
from .recommendations import RecommendationEngine
from .products import ProductRecommendationEngine

__all__ = [
    'AIClient',
    'VisionAnalyzer',
    'RecommendationEngine',
    'ProductRecommendationEngine',
]
