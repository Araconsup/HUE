"""
HUE Core URL Configuration
Routes for web app, PWA assets, and REST API endpoints.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Primary PWA Web Views
    path('', views.index_view, name='index'),
    path('manifest.json', views.manifest_view, name='pwa_manifest'),
    path('sw.js', views.service_worker_view, name='pwa_sw'),

    # AI Vision Analysis APIs
    path('api/ai/analyze/face/', views.analyze_face_api, name='api_analyze_face'),
    path('api/ai/analyze/outfit/', views.analyze_outfit_api, name='api_analyze_outfit'),
    path('api/ai/analyze/combined/', views.analyze_combined_api, name='api_analyze_combined'),

    # Product Search & Matching APIs
    path('api/products/search/', views.product_search_api, name='api_product_search'),
    path('api/products/match/', views.product_match_api, name='api_product_match'),

    # Look Customization & Saved Looks APIs
    path('api/looks/generate/', views.generate_look_api, name='api_looks_generate'),
    path('api/looks/save/', views.save_look_api, name='api_looks_save'),
    path('api/looks/saved/', views.saved_looks_list_api, name='api_looks_saved_list'),

    # User's "My Makeup Bag" APIs
    path('api/user/products/', views.user_products_api, name='api_user_products'),
    path('api/user/products/<int:item_id>/', views.user_products_api, name='api_user_products_detail'),
]
