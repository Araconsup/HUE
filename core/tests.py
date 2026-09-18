"""
HUE Comprehensive Test Suite
Verifies AI vision validation, recommendation engine, product matching, and REST APIs.
"""

import io
import json
from PIL import Image
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import (
    ProductBrand, ProductCategory, Product, ProductShade,
    UserProduct, AnalysisSession, SavedLook
)
from core.ai.vision import VisionAnalyzer
from core.ai.recommendations import RecommendationEngine
from core.ai.products import ProductRecommendationEngine
from core.ai.validators import sanitize_beauty_text, validate_color_dict, validate_confidence


def create_test_image_bytes(width=400, height=400, color=(200, 150, 130)):
    """Helper to generate in-memory test image bytes."""
    buf = io.BytesIO()
    img = Image.new('RGB', (width, height), color)
    img.save(buf, format='JPEG')
    return buf.getvalue()


class AIVisionValidationTests(TestCase):
    """Tests for Stage 1 Vision Validation & Safety filters."""

    def setUp(self):
        self.analyzer = VisionAnalyzer()

    def test_reject_extremely_dark_image(self):
        """Images that are too dark should be rejected with actionable guidance."""
        dark_bytes = create_test_image_bytes(color=(5, 5, 5))
        result = self.analyzer.validate_image(dark_bytes)
        self.assertFalse(result.is_usable)
        self.assertIn("too low", result.message.lower())

    def test_reject_tiny_resolution_image(self):
        """Images below minimum resolution should be rejected."""
        tiny_bytes = create_test_image_bytes(width=80, height=80)
        result = self.analyzer.validate_image(tiny_bytes)
        self.assertFalse(result.is_usable)
        self.assertIn("resolution", result.message.lower())

    def test_accept_well_lit_image(self):
        """Well-lit, adequately sized images should pass validation."""
        valid_bytes = create_test_image_bytes(width=600, height=600, color=(210, 160, 140))
        result = self.analyzer.validate_image(valid_bytes)
        self.assertTrue(result.is_usable)

    def test_sanitize_diagnostic_terms(self):
        """Ensures medical / sensitive terms are neutralized."""
        unsafe = "The model diagnosed severe acne, rosacea, and eczema on the caucasian face."
        safe = sanitize_beauty_text(unsafe)
        self.assertNotIn("acne", safe.lower())
        self.assertNotIn("rosacea", safe.lower())
        self.assertNotIn("caucasian", safe.lower())
        self.assertIn("complexion variation", safe)

    def test_validate_color_dict(self):
        """Ensures hex colors are properly formatted."""
        c = validate_color_dict({"color_name": "Peach", "hex": "#FF9988", "temperature": "warm"})
        self.assertEqual(c["hex"], "#FF9988")

        bad = validate_color_dict({"color_name": "Invalid", "hex": "not-a-hex"})
        self.assertEqual(bad["hex"], "#C48D7F")  # fallback default


class RecommendationEngineTests(TestCase):
    """Tests for recommendation generation and routine ordering."""

    def test_generate_structured_recommendations(self):
        engine = RecommendationEngine()
        result = engine.generate_recommendations(mode='face')

        self.assertIn('look_name', result)
        self.assertIn('recommendations', result)
        self.assertIn('application_steps', result)
        self.assertIn('confidence', result)

        recs = result['recommendations']
        for cat in ['base', 'blush', 'eyeshadow', 'lips']:
            self.assertIn(cat, recs)
            self.assertIn('product_direction', recs[cat])
            self.assertIn('color', recs[cat])

        steps = result['application_steps']
        self.assertGreaterEqual(len(steps), 8)
        self.assertEqual(steps[0]['category'], 'Base')


class ProductMatchingTests(TestCase):
    """Tests for product searching, matching, and 'Use What I Own' routine."""

    def setUp(self):
        self.brand = ProductBrand.objects.create(name="Rare Beauty", slug="rare-beauty")
        self.cat_blush = ProductCategory.objects.create(name="Blush", slug="blush", step_order=4)
        self.product = Product.objects.create(
            brand=self.brand,
            category=self.cat_blush,
            name="Soft Pinch Liquid Blush",
            finish="Dewy Radiant",
            price=23.00
        )
        self.shade = ProductShade.objects.create(
            product=self.product,
            name="Hope",
            shade_code="HP",
            hex_color="#D67D78",
            undertone="neutral-warm"
        )
        self.engine = ProductRecommendationEngine()

    def test_product_search(self):
        results = self.engine.search_products(query="Rare")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['brand'], "Rare Beauty")

        # Category filter
        results_cat = self.engine.search_products(category_slug="blush")
        self.assertEqual(len(results_cat), 1)

    def test_product_matching_score(self):
        match = self.engine.match_product(
            product=self.product,
            shade=self.shade,
            recommended_category="blush",
            recommendation_details={
                "product_direction": "Dewy peach liquid blush",
                "color": {"temperature": "warm"}
            }
        )
        self.assertGreaterEqual(match['compatibility']['score'], 0.85)
        self.assertIn("Blush", match['compatibility']['role'])

    def test_use_what_i_own_routine(self):
        session_key = "test_user_session_123"
        UserProduct.objects.create(
            session_key=session_key,
            product=self.product,
            shade=self.shade,
            is_in_makeup_bag=True
        )

        steps = [
            {"step_number": 1, "category": "Base", "title": "Base Prep", "guidance": "Apply base"},
            {"step_number": 4, "category": "Blush", "title": "Cheek Flush", "guidance": "Apply blush"},
        ]

        routine = self.engine.generate_use_what_i_own_routine(
            session_key=session_key,
            recommendations={},
            application_steps=steps
        )

        self.assertEqual(routine['owned_products_matched'], 1)
        blush_step = routine['customized_routine'][1]
        self.assertIsNotNone(blush_step['owned_product'])
        self.assertEqual(blush_step['owned_product']['name'], "Soft Pinch Liquid Blush")


class APIEndpointsTests(TestCase):
    """Integration tests for all REST API endpoints."""

    def setUp(self):
        self.client = Client()
        self.brand = ProductBrand.objects.create(name="MAC", slug="mac")
        self.cat = ProductCategory.objects.create(name="Lips", slug="lips", step_order=10)
        self.product = Product.objects.create(
            brand=self.brand,
            category=self.cat,
            name="Retro Matte Lipstick",
            price=23.00
        )
        self.shade = ProductShade.objects.create(
            product=self.product,
            name="Velvet Teddy",
            hex_color="#B57B6C",
            undertone="neutral-warm"
        )

    def test_index_view(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "HUE")
        self.assertContains(resp, "What are you styling today?")

    def test_manifest_and_service_worker(self):
        resp_m = self.client.get('/manifest.json')
        self.assertEqual(resp_m.status_code, 200)
        self.assertIn('HUE', resp_m.json()['name'])

        resp_sw = self.client.get('/sw.js')
        self.assertEqual(resp_sw.status_code, 200)
        self.assertIn('hue-cache', resp_sw.content.decode())

    def test_analyze_face_endpoint(self):
        img_bytes = create_test_image_bytes(500, 500)
        file = SimpleUploadedFile("face.jpg", img_bytes, content_type="image/jpeg")

        resp = self.client.post('/api/ai/analyze/face/', {'face_image': file})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['mode'], 'face')
        self.assertIn('session_id', data)
        self.assertIn('recommendations', data['data'])

        # Verify session saved in DB
        self.assertTrue(AnalysisSession.objects.filter(id=data['session_id']).exists())

    def test_analyze_outfit_endpoint(self):
        img_bytes = create_test_image_bytes(500, 500)
        file = SimpleUploadedFile("outfit.jpg", img_bytes, content_type="image/jpeg")

        resp = self.client.post('/api/ai/analyze/outfit/', {'outfit_image': file})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['mode'], 'outfit')

    def test_analyze_combined_endpoint(self):
        face_bytes = create_test_image_bytes(500, 500)
        outfit_bytes = create_test_image_bytes(500, 500)
        face_file = SimpleUploadedFile("face.jpg", face_bytes, content_type="image/jpeg")
        outfit_file = SimpleUploadedFile("outfit.jpg", outfit_bytes, content_type="image/jpeg")

        resp = self.client.post('/api/ai/analyze/combined/', {
            'face_image': face_file,
            'outfit_image': outfit_file
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['mode'], 'combined')

    def test_user_products_bag_lifecycle(self):
        # Add to bag
        resp_add = self.client.post('/api/user/products/', json.dumps({
            'product_id': self.product.id,
            'shade_id': self.shade.id
        }), content_type='application/json')
        self.assertEqual(resp_add.status_code, 201)
        item_id = resp_add.json()['id']

        # List bag
        resp_list = self.client.get('/api/user/products/')
        self.assertEqual(resp_list.status_code, 200)
        self.assertEqual(resp_list.json()['count'], 1)

        # Delete from bag
        resp_del = self.client.delete(f'/api/user/products/{item_id}/')
        self.assertEqual(resp_del.status_code, 200)

        # Confirm empty
        resp_list2 = self.client.get('/api/user/products/')
        self.assertEqual(resp_list2.json()['count'], 0)

    def test_save_and_retrieve_looks(self):
        resp_save = self.client.post('/api/looks/save/', json.dumps({
            'title': 'My Evening Glam',
            'look_name': 'Warm Sunset Glow',
            'mode': 'combined',
            'routine_data': [{'step_number': 1, 'category': 'Base'}]
        }), content_type='application/json')
        self.assertEqual(resp_save.status_code, 201)

        resp_list = self.client.get('/api/looks/saved/')
        self.assertEqual(resp_list.status_code, 200)
        self.assertEqual(resp_list.json()['count'], 1)
        self.assertEqual(resp_list.json()['looks'][0]['title'], 'My Evening Glam')
