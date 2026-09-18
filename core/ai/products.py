"""
HUE Product Recommendation & Matching Engine
Matches visual makeup recommendations with cosmetic products and powers "Use What I Own" mode.
"""

import logging
from typing import Dict, Any, List, Optional
from django.db.models import Q
from core.models import Product, ProductShade, UserProduct
from .client import AIClient
from .prompts import PRODUCT_MATCHING_PROMPT, BASE_VISION_SYSTEM_PROMPT

logger = logging.getLogger('hue.ai.products')


class ProductRecommendationEngine:
    """
    Evaluates compatibility between recommended makeup styles and products.
    Powers product matching and the personalized 'Use What I Own' routine.
    """

    def __init__(self, client: AIClient = None):
        self.client = client or AIClient()

    def search_products(
        self,
        query: str = "",
        category_slug: Optional[str] = None,
        brand_slug: Optional[str] = None,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Fast catalog search supporting brand, category, name, and shade matching."""
        qs = Product.objects.filter(is_active=True).select_related('brand', 'category').prefetch_related('shades')

        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if brand_slug:
            qs = qs.filter(brand__slug=brand_slug)

        if query:
            q_clean = query.strip()
            qs = qs.filter(
                Q(name__icontains=q_clean) |
                Q(brand__name__icontains=q_clean) |
                Q(subcategory__icontains=q_clean) |
                Q(shades__name__icontains=q_clean)
            ).distinct()

        results = []
        for p in qs[:limit]:
            shades_data = [
                {
                    "id": s.id,
                    "name": s.name,
                    "shade_code": s.shade_code,
                    "hex_color": s.hex_color,
                    "undertone": s.undertone
                }
                for s in p.shades.all()
            ]
            results.append({
                "id": p.id,
                "name": p.name,
                "brand": p.brand.name,
                "brand_slug": p.brand.slug,
                "category": p.category.name,
                "category_slug": p.category.slug,
                "subcategory": p.subcategory,
                "finish": p.finish,
                "description": p.description,
                "price": float(p.price) if p.price else None,
                "currency": p.currency,
                "image_url": p.display_image,
                "shades": shades_data
            })
        return results

    def match_product(
        self,
        product: Product,
        shade: Optional[ProductShade],
        recommended_category: str,
        recommendation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates compatibility between a specific product/shade and a recommended step.
        """
        rec_dir = recommendation_details.get("product_direction", "")
        color_info = recommendation_details.get("color", {})
        color_name = color_info.get("color_name", "") if isinstance(color_info, dict) else ""
        shade_undertone = shade.undertone if shade else "neutral"

        # Heuristic compatibility check
        score = 0.88
        role = f"Recommended {recommended_category.title()} Anchor"
        usage = f"Apply as directed in your HUE routine: {recommendation_details.get('placement', 'balanced application')}."
        reason = f"The {product.finish.lower() if product.finish else 'smooth'} finish and {shade.name if shade else 'tone'} shade align cleanly with your visual styling."

        # If categories align perfectly, boost score
        prod_cat_slug = product.category.slug.lower()
        if recommended_category.lower() in prod_cat_slug or prod_cat_slug in recommended_category.lower():
            score += 0.05

        # Check undertone harmony
        target_temp = color_info.get("temperature", "neutral").lower() if isinstance(color_info, dict) else "neutral"
        if target_temp in shade_undertone.lower() or "neutral" in shade_undertone.lower():
            score += 0.03
            reason += " Undertone balance directly matches your skin's visible harmony."

        score = min(0.99, max(0.65, round(score, 2)))

        return {
            "product": {
                "id": product.id,
                "name": product.name,
                "brand": product.brand.name,
                "category": product.category.name,
                "shade": shade.name if shade else "",
                "shade_hex": shade.hex_color if shade else "",
                "image_url": product.display_image
            },
            "compatibility": {
                "score": score,
                "role": role,
                "usage": usage,
                "reason": reason
            }
        }

    def generate_use_what_i_own_routine(
        self,
        session_key: str,
        recommendations: Dict[str, Any],
        application_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Assembles a complete makeup routine prioritizing products already saved in the user's makeup bag.
        """
        user_products = UserProduct.objects.filter(
            session_key=session_key,
            is_in_makeup_bag=True
        ).select_related('product__brand', 'product__category', 'shade')

        # Map owned products by category slug
        owned_by_category: Dict[str, List[UserProduct]] = {}
        for up in user_products:
            cat_slug = up.product.category.slug.lower()
            owned_by_category.setdefault(cat_slug, []).append(up)

        customized_steps = []
        matched_count = 0

        for step in application_steps:
            cat = step.get("category", "").lower()
            step_copy = dict(step)

            # Find matching user product in category
            matched_up = None
            for owned_cat, prods in owned_by_category.items():
                if cat in owned_cat or owned_cat in cat or (cat == "base" and "foundation" in owned_cat):
                    matched_up = prods[0]
                    break

            if matched_up:
                matched_count += 1
                match_info = self.match_product(
                    product=matched_up.product,
                    shade=matched_up.shade,
                    recommended_category=step.get("category", ""),
                    recommendation_details=step
                )
                step_copy["owned_product"] = {
                    "user_product_id": matched_up.id,
                    "brand": matched_up.product.brand.name,
                    "name": matched_up.product.name,
                    "shade": matched_up.shade.name if matched_up.shade else matched_up.custom_shade_name,
                    "shade_hex": matched_up.shade.hex_color if matched_up.shade else "#C48D7F",
                    "image_url": matched_up.product.display_image,
                    "compatibility_score": match_info["compatibility"]["score"],
                    "usage_guidance": match_info["compatibility"]["usage"],
                    "why_selected": match_info["compatibility"]["reason"]
                }
            else:
                step_copy["owned_product"] = None

            customized_steps.append(step_copy)

        return {
            "total_steps": len(customized_steps),
            "owned_products_matched": matched_count,
            "coverage_percentage": round((matched_count / max(1, len(customized_steps))) * 100),
            "customized_routine": customized_steps
        }
