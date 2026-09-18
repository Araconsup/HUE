"""
HUE API Views & Controllers
Clean endpoints for vision analysis, styling recommendations, product catalog, and user makeup bag.
"""

import json
import logging
import uuid
from typing import Optional, Tuple
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, get_object_or_404
from django.core.files.base import ContentFile

from .models import (
    Product, ProductShade, ProductCategory, ProductBrand,
    UserProduct, AnalysisSession, AnalysisImage, FaceAnalysis,
    OutfitAnalysis, MakeupRecommendation, SavedLook, SavedLookProduct
)
from .ai.gateway import ImageProcessor
from .ai.vision import VisionAnalyzer
from .ai.recommendations import RecommendationEngine
from .ai.products import ProductRecommendationEngine

logger = logging.getLogger('hue.api')


def _get_or_create_session_key(request: HttpRequest) -> str:
    """Ensures a persistent session key exists for guest or authenticated users."""
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _extract_image_bytes(request: HttpRequest, file_key: str = 'image') -> Tuple[Optional[bytes], Optional[str]]:
    """Extracts raw image bytes from either multipart upload or JSON base64 data URI."""
    if file_key in request.FILES:
        uploaded_file = request.FILES[file_key]
        return uploaded_file.read(), uploaded_file.name

    # Check for base64 JSON payload
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            data_uri = body.get(file_key) or body.get('image_data') or body.get('data_uri')
            if data_uri and ',' in data_uri:
                import base64
                header, encoded = data_uri.split(',', 1)
                return base64.b64decode(encoded), 'upload.jpg'
        except Exception:
            pass

    return None, None


# --------------------------------------------------------------------------
# Main Web App / PWA Views
# --------------------------------------------------------------------------

def index_view(request: HttpRequest) -> HttpResponse:
    """Renders the primary HUE beauty styling PWA application."""
    session_key = _get_or_create_session_key(request)
    bag_count = UserProduct.objects.filter(session_key=session_key, is_in_makeup_bag=True).count()
    categories = ProductCategory.objects.all().order_by('step_order')
    brands = ProductBrand.objects.all().order_by('name')

    context = {
        'bag_count': bag_count,
        'categories': categories,
        'brands': brands,
    }
    return render(request, 'index.html', context)


def manifest_view(request: HttpRequest) -> HttpResponse:
    """PWA Web App Manifest."""
    manifest = {
        "name": "HUE — AI Makeup Intelligence",
        "short_name": "HUE",
        "description": "Intelligent AI Vision Makeup Assistant & Visual Styling Engine",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0D0C10",
        "theme_color": "#18171E",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/static/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    }
    return HttpResponse(json.dumps(manifest), content_type='application/manifest+json')


def service_worker_view(request: HttpRequest) -> HttpResponse:
    """PWA Service Worker script (Network-first with offline cache fallback)."""
    sw_code = """
const CACHE_NAME = 'hue-cache-v2';
const STATIC_ASSETS = [
  '/',
  '/static/css/app.css',
  '/static/js/app.js',
  '/manifest.json'
];

self.addEventListener('install', (evt) => {
  evt.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (evt) => {
  evt.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((k) => {
          if (k !== CACHE_NAME) return caches.delete(k);
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (evt) => {
  if (evt.request.method !== 'GET' || evt.request.url.includes('/api/')) {
    return;
  }
  evt.respondWith(
    fetch(evt.request)
      .then((resp) => {
        const respClone = resp.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(evt.request, respClone));
        return resp;
      })
      .catch(() => caches.match(evt.request))
  );
});
"""
    return HttpResponse(sw_code.strip(), content_type='application/javascript')


# --------------------------------------------------------------------------
# AI Vision Analysis Endpoints
# --------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["POST"])
def analyze_face_api(request: HttpRequest) -> JsonResponse:
    """
    POST /api/ai/analyze/face/
    Stage 1 Validation -> Face Analysis -> Recommendation Engine
    """
    session_key = _get_or_create_session_key(request)
    img_bytes, filename = _extract_image_bytes(request, 'face_image')
    if not img_bytes:
        img_bytes, filename = _extract_image_bytes(request, 'image')

    if not img_bytes:
        return JsonResponse({"error": "No face image provided. Please upload a photo."}, status=400)

    analyzer = VisionAnalyzer()
    validation = analyzer.validate_image(img_bytes, requested_mode='face')
    if not validation.is_usable:
        return JsonResponse({
            "success": False,
            "error_type": "validation_failed",
            "message": validation.message,
            "details": validation.details
        }, status=422)

    # Process and get data URI
    success, data_uri, compressed_bytes, meta = ImageProcessor.process_image(img_bytes)

    # Stage 2: Face Feature Analysis
    face_data = analyzer.analyze_face(data_uri)

    # Stage 3: Recommendation Engine
    rec_engine = RecommendationEngine()
    recommendation_data = rec_engine.generate_recommendations(
        mode='face',
        face_analysis=face_data,
        image_data_uris=[data_uri]
    )

    # Persist session & analysis models
    user = request.user if request.user.is_authenticated else None
    session_obj = AnalysisSession.objects.create(
        user=user,
        session_key=session_key,
        mode='face',
        look_name=recommendation_data.get('look_name', 'Bespoke Face Styling'),
        summary=recommendation_data.get('summary', ''),
        confidence_overall=recommendation_data.get('confidence', {}).get('overall', 0.90),
        confidence_data=recommendation_data.get('confidence', {}),
        raw_ai_response=recommendation_data
    )

    AnalysisImage.objects.create(
        session=session_obj,
        image_type='face',
        image_data_uri=data_uri,
        width=meta.get('width'),
        height=meta.get('height'),
        is_validated=True,
        validation_notes=validation.message
    )

    FaceAnalysis.objects.create(
        session=session_obj,
        image_quality=face_data.get('image_quality', {}),
        face_visibility=face_data.get('face_visibility', {}),
        complexion_observations=face_data.get('complexion_observations', {}),
        visible_undertone_indicators=face_data.get('visible_undertone_indicators', {}),
        face_shape_estimate=face_data.get('face_shape_estimate', {}),
        eye_area=face_data.get('eye_area', {}),
        lip_area=face_data.get('lip_area', {}),
        brow_area=face_data.get('brow_area', {}),
        existing_makeup=face_data.get('existing_makeup', {}),
        color_harmony=face_data.get('color_harmony', {}),
        recommended_makeup_direction=face_data.get('recommended_makeup_direction', {})
    )

    # Save individual recommendation cards
    for cat_name, cat_val in recommendation_data.get('recommendations', {}).items():
        color_info = cat_val.get('color', {})
        MakeupRecommendation.objects.create(
            session=session_obj,
            category=cat_name,
            product_direction=cat_val.get('product_direction', ''),
            color_name=color_info.get('color_name', ''),
            hex_color=color_info.get('hex', '#C48D7F'),
            temperature=color_info.get('temperature', ''),
            saturation=color_info.get('saturation', ''),
            brightness=color_info.get('brightness', ''),
            finish=cat_val.get('finish', ''),
            intensity=cat_val.get('intensity', ''),
            placement=cat_val.get('placement', ''),
            reasoning=cat_val.get('reasoning', ''),
            extra_details=cat_val.get('extra_details', {})
        )

    return JsonResponse({
        "success": True,
        "session_id": str(session_obj.id),
        "mode": "face",
        "data": recommendation_data
    })


@csrf_exempt
@require_http_methods(["POST"])
def analyze_outfit_api(request: HttpRequest) -> JsonResponse:
    """
    POST /api/ai/analyze/outfit/
    Stage 1 Validation -> Outfit Analysis -> Recommendation Engine
    """
    session_key = _get_or_create_session_key(request)
    img_bytes, filename = _extract_image_bytes(request, 'outfit_image')
    if not img_bytes:
        img_bytes, filename = _extract_image_bytes(request, 'image')

    if not img_bytes:
        return JsonResponse({"error": "No outfit image provided. Please upload a photo."}, status=400)

    analyzer = VisionAnalyzer()
    validation = analyzer.validate_image(img_bytes, requested_mode='outfit')
    if not validation.is_usable:
        return JsonResponse({
            "success": False,
            "error_type": "validation_failed",
            "message": validation.message,
            "details": validation.details
        }, status=422)

    success, data_uri, compressed_bytes, meta = ImageProcessor.process_image(img_bytes)

    # Stage 2: Outfit Visual Analysis
    outfit_data = analyzer.analyze_outfit(data_uri)

    # Stage 3: Recommendation Engine
    rec_engine = RecommendationEngine()
    recommendation_data = rec_engine.generate_recommendations(
        mode='outfit',
        outfit_analysis=outfit_data,
        image_data_uris=[data_uri]
    )

    user = request.user if request.user.is_authenticated else None
    session_obj = AnalysisSession.objects.create(
        user=user,
        session_key=session_key,
        mode='outfit',
        look_name=recommendation_data.get('look_name', 'Outfit-Harmonized Styling'),
        summary=recommendation_data.get('summary', ''),
        confidence_overall=recommendation_data.get('confidence', {}).get('overall', 0.92),
        confidence_data=recommendation_data.get('confidence', {}),
        raw_ai_response=recommendation_data
    )

    AnalysisImage.objects.create(
        session=session_obj,
        image_type='outfit',
        image_data_uri=data_uri,
        width=meta.get('width'),
        height=meta.get('height'),
        is_validated=True,
        validation_notes=validation.message
    )

    OutfitAnalysis.objects.create(
        session=session_obj,
        dominant_colors=outfit_data.get('dominant_colors', []),
        secondary_colors=outfit_data.get('secondary_colors', []),
        pattern=outfit_data.get('pattern', ''),
        contrast=outfit_data.get('contrast', ''),
        temperature=outfit_data.get('temperature', ''),
        saturation=outfit_data.get('saturation', ''),
        brightness=outfit_data.get('brightness', ''),
        style=outfit_data.get('style', ''),
        formality=outfit_data.get('formality', ''),
        overall_aesthetic=outfit_data.get('overall_aesthetic', ''),
        raw_details=outfit_data
    )

    return JsonResponse({
        "success": True,
        "session_id": str(session_obj.id),
        "mode": "outfit",
        "data": recommendation_data
    })


@csrf_exempt
@require_http_methods(["POST"])
def analyze_combined_api(request: HttpRequest) -> JsonResponse:
    """
    POST /api/ai/analyze/combined/
    Stage 1 Validation on both -> Combined Visual Harmony Analysis -> Recommendation Engine
    """
    session_key = _get_or_create_session_key(request)
    face_bytes, _ = _extract_image_bytes(request, 'face_image')
    outfit_bytes, _ = _extract_image_bytes(request, 'outfit_image')

    if not face_bytes or not outfit_bytes:
        return JsonResponse({
            "error": "Both face and outfit images are required for combined analysis."
        }, status=400)

    analyzer = VisionAnalyzer()

    # Validate Face Image
    face_val = analyzer.validate_image(face_bytes, requested_mode='face')
    if not face_val.is_usable:
        return JsonResponse({
            "success": False,
            "error_type": "face_validation_failed",
            "message": f"Face photo check: {face_val.message}",
            "details": face_val.details
        }, status=422)

    # Validate Outfit Image
    outfit_val = analyzer.validate_image(outfit_bytes, requested_mode='outfit')
    if not outfit_val.is_usable:
        return JsonResponse({
            "success": False,
            "error_type": "outfit_validation_failed",
            "message": f"Outfit photo check: {outfit_val.message}",
            "details": outfit_val.details
        }, status=422)

    _, face_uri, _, face_meta = ImageProcessor.process_image(face_bytes)
    _, outfit_uri, _, outfit_meta = ImageProcessor.process_image(outfit_bytes)

    # Combined Visual Analysis
    combined_raw = analyzer.analyze_combined(face_uri, outfit_uri)

    rec_engine = RecommendationEngine()
    recommendation_data = rec_engine.generate_recommendations(
        mode='combined',
        combined_data=combined_raw,
        image_data_uris=[face_uri, outfit_uri]
    )

    user = request.user if request.user.is_authenticated else None
    session_obj = AnalysisSession.objects.create(
        user=user,
        session_key=session_key,
        mode='combined',
        look_name=recommendation_data.get('look_name', 'Complete Harmony Styling'),
        summary=recommendation_data.get('summary', ''),
        confidence_overall=recommendation_data.get('confidence', {}).get('overall', 0.94),
        confidence_data=recommendation_data.get('confidence', {}),
        raw_ai_response=recommendation_data
    )

    AnalysisImage.objects.create(
        session=session_obj,
        image_type='face',
        image_data_uri=face_uri,
        width=face_meta.get('width'),
        height=face_meta.get('height'),
        is_validated=True
    )
    AnalysisImage.objects.create(
        session=session_obj,
        image_type='outfit',
        image_data_uri=outfit_uri,
        width=outfit_meta.get('width'),
        height=outfit_meta.get('height'),
        is_validated=True
    )

    return JsonResponse({
        "success": True,
        "session_id": str(session_obj.id),
        "mode": "combined",
        "data": recommendation_data
    })


# --------------------------------------------------------------------------
# Product Search & Matching Endpoints
# --------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["POST", "GET"])
def product_search_api(request: HttpRequest) -> JsonResponse:
    """
    POST or GET /api/products/search/
    Live search supporting brand, category, name, and shade matching.
    """
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except Exception:
            body = {}
        query = body.get('query', '')
        category_slug = body.get('category')
        brand_slug = body.get('brand')
        limit = int(body.get('limit', 30))
    else:
        query = request.GET.get('q', '')
        category_slug = request.GET.get('category')
        brand_slug = request.GET.get('brand')
        limit = int(request.GET.get('limit', 30))

    engine = ProductRecommendationEngine()
    products = engine.search_products(
        query=query,
        category_slug=category_slug,
        brand_slug=brand_slug,
        limit=limit
    )

    return JsonResponse({
        "success": True,
        "total": len(products),
        "products": products
    })


@csrf_exempt
@require_http_methods(["POST"])
def product_match_api(request: HttpRequest) -> JsonResponse:
    """
    POST /api/products/match/
    Evaluates compatibility between a selected product and a recommended makeup step.
    """
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    product_id = body.get('product_id')
    shade_id = body.get('shade_id')
    category = body.get('category', 'Base')
    rec_details = body.get('recommendation', {})

    if not product_id:
        return JsonResponse({"error": "product_id is required"}, status=400)

    try:
        product = Product.objects.select_related('brand', 'category').get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    shade = None
    if shade_id:
        shade = ProductShade.objects.filter(id=shade_id, product=product).first()

    engine = ProductRecommendationEngine()
    match_result = engine.match_product(
        product=product,
        shade=shade,
        recommended_category=category,
        recommendation_details=rec_details
    )

    return JsonResponse({
        "success": True,
        "match": match_result
    })


# --------------------------------------------------------------------------
# "Use What I Own" & Routine Generation Endpoints
# --------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["POST"])
def generate_look_api(request: HttpRequest) -> JsonResponse:
    """
    POST /api/looks/generate/
    Generates tailored routine, supporting "Use What I Own" mode.
    """
    session_key = _get_or_create_session_key(request)
    try:
        body = json.loads(request.body)
    except Exception:
        body = {}

    use_my_products = body.get('use_my_products', False)
    recommendations = body.get('recommendations', {})
    application_steps = body.get('application_steps', [])

    if not application_steps:
        # Generate default steps if not passed
        valid, default_resp, _ = RecommendationEngine().client._simulate_vision_response("", [])
        application_steps = default_resp.get("application_steps", [])
        recommendations = default_resp.get("recommendations", {})

    if use_my_products:
        engine = ProductRecommendationEngine()
        result = engine.generate_use_what_i_own_routine(
            session_key=session_key,
            recommendations=recommendations,
            application_steps=application_steps
        )
        return JsonResponse({
            "success": True,
            "mode": "use_my_products",
            **result
        })

    return JsonResponse({
        "success": True,
        "mode": "standard",
        "customized_routine": application_steps
    })


# --------------------------------------------------------------------------
# User's Makeup Bag ("My Makeup Bag") Endpoints
# --------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["GET", "POST", "DELETE"])
def user_products_api(request: HttpRequest, item_id: Optional[int] = None) -> JsonResponse:
    """
    GET  /api/user/products/       -> List items in bag
    POST /api/user/products/       -> Add item to bag
    DELETE /api/user/products/<id>/ -> Remove item from bag
    """
    session_key = _get_or_create_session_key(request)
    user = request.user if request.user.is_authenticated else None

    if request.method == 'GET':
        items = UserProduct.objects.filter(
            session_key=session_key,
            is_in_makeup_bag=True
        ).select_related('product__brand', 'product__category', 'shade')

        data = [
            {
                "id": up.id,
                "product_id": up.product.id,
                "brand": up.product.brand.name,
                "name": up.product.name,
                "category": up.product.category.name,
                "category_slug": up.product.category.slug,
                "shade": up.shade.name if up.shade else up.custom_shade_name,
                "shade_hex": up.shade.hex_color if up.shade else "#C48D7F",
                "image_url": up.product.display_image,
                "notes": up.notes
            }
            for up in items
        ]
        return JsonResponse({"success": True, "count": len(data), "products": data})

    elif request.method == 'POST':
        try:
            body = json.loads(request.body)
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        product_id = body.get('product_id')
        shade_id = body.get('shade_id')
        notes = body.get('notes', '')

        if not product_id:
            return JsonResponse({"error": "product_id is required"}, status=400)

        product = get_object_or_404(Product, id=product_id)
        shade = ProductShade.objects.filter(id=shade_id, product=product).first() if shade_id else None

        up, created = UserProduct.objects.get_or_create(
            session_key=session_key,
            product=product,
            shade=shade,
            defaults={
                "user": user,
                "notes": notes,
                "is_in_makeup_bag": True
            }
        )
        if not created and not up.is_in_makeup_bag:
            up.is_in_makeup_bag = True
            up.save()

        return JsonResponse({
            "success": True,
            "created": created,
            "id": up.id,
            "message": f"Added {product.name} to My Makeup Bag"
        }, status=201)

    elif request.method == 'DELETE':
        if not item_id:
            return JsonResponse({"error": "Item ID required"}, status=400)

        deleted, _ = UserProduct.objects.filter(id=item_id, session_key=session_key).delete()
        if deleted:
            return JsonResponse({"success": True, "message": "Product removed from makeup bag"})
        return JsonResponse({"error": "Item not found in your bag"}, status=404)


# --------------------------------------------------------------------------
# Saved Looks Endpoints
# --------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["POST"])
def save_look_api(request: HttpRequest) -> JsonResponse:
    """
    POST /api/looks/save/
    Saves a completed customized makeup look.
    """
    session_key = _get_or_create_session_key(request)
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    title = body.get('title', 'My HUE Look')
    look_name = body.get('look_name', 'Bespoke Look')
    description = body.get('description', '')
    mode = body.get('mode', 'face')
    routine_data = body.get('routine_data', [])
    visual_summary = body.get('visual_summary', {})

    user = request.user if request.user.is_authenticated else None
    saved_look = SavedLook.objects.create(
        user=user,
        session_key=session_key,
        title=title,
        look_name=look_name,
        description=description,
        mode=mode,
        routine_data=routine_data,
        visual_summary=visual_summary
    )

    # Optionally associate matched products
    for step in routine_data:
        owned_prod = step.get('owned_product')
        if owned_prod and 'product_id' in owned_prod:
            prod_id = owned_prod['product_id']
            prod = Product.objects.filter(id=prod_id).first()
            if prod:
                SavedLookProduct.objects.create(
                    saved_look=saved_look,
                    product=prod,
                    step_name=step.get('category', 'Step'),
                    usage_notes=owned_prod.get('usage_guidance', '')
                )

    return JsonResponse({
        "success": True,
        "saved_look_id": str(saved_look.id),
        "message": f"Saved '{saved_look.title}' successfully"
    }, status=201)


@csrf_exempt
@require_http_methods(["GET"])
def saved_looks_list_api(request: HttpRequest) -> JsonResponse:
    """GET /api/looks/saved/ -> List all saved looks."""
    session_key = _get_or_create_session_key(request)
    looks = SavedLook.objects.filter(session_key=session_key).order_by('-created_at')

    data = [
        {
            "id": str(l.id),
            "title": l.title,
            "look_name": l.look_name,
            "description": l.description,
            "mode": l.mode,
            "routine_steps_count": len(l.routine_data) if isinstance(l.routine_data, list) else 0,
            "created_at": l.created_at.strftime('%b %d, %Y')
        }
        for l in looks
    ]
    return JsonResponse({"success": True, "count": len(data), "looks": data})
