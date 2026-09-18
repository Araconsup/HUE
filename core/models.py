"""
HUE Core Data Models
Scalable schema for AI vision beauty intelligence, product matching, and styling.
"""

from django.db import models
from django.contrib.auth.models import User
import uuid


class UserProfile(models.Model):
    """Optional user profile for personalized beauty preferences."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', null=True, blank=True)
    session_key = models.CharField(max_length=64, db_index=True, blank=True)
    display_name = models.CharField(max_length=100, blank=True)
    skin_type_preference = models.CharField(max_length=50, blank=True, help_text="e.g. dry, oily, combination, normal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name or f"Profile ({self.session_key[:8]})"


class ProductBrand(models.Model):
    """Cosmetic product brand."""
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    """Cosmetic category (e.g., Base, Blush, Bronzer, Highlighter, Eyeshadow, Eyeliner, Mascara, Brows, Lips)."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    step_order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['step_order', 'name']
        verbose_name_plural = 'Product categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    """Specific cosmetic product."""
    brand = models.ForeignKey(ProductBrand, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    subcategory = models.CharField(max_length=100, blank=True, help_text="e.g. Liquid Blush, Powder Foundation")
    finish = models.CharField(max_length=60, blank=True, help_text="e.g. Matte, Dewy, Satin, Radiant, Shimmer")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    image_url = models.URLField(blank=True, help_text="Fallback web image URL")
    product_url = models.URLField(blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['brand__name', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.brand.name} — {self.name}"

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url or ''


class ProductShade(models.Model):
    """Specific shade of a cosmetic product."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='shades')
    name = models.CharField(max_length=120)
    shade_code = models.CharField(max_length=60, blank=True)
    hex_color = models.CharField(max_length=7, default='#C48D7F', help_text="HEX color approximation")
    undertone = models.CharField(max_length=40, blank=True, help_text="warm, cool, neutral, olive")
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.product.name} ({self.name})"


class UserProduct(models.Model):
    """Products saved by the user into 'My Makeup Bag'."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='saved_products')
    session_key = models.CharField(max_length=64, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='user_instances')
    shade = models.ForeignKey(ProductShade, on_delete=models.SET_NULL, null=True, blank=True)
    custom_shade_name = models.CharField(max_length=100, blank=True)
    notes = models.CharField(max_length=250, blank=True)
    is_in_makeup_bag = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        shade_str = f" - {self.shade.name}" if self.shade else ""
        return f"{self.product.brand.name} {self.product.name}{shade_str}"


class AnalysisSession(models.Model):
    """Record of an AI vision styling session."""
    MODE_CHOICES = [
        ('face', 'Face Analysis'),
        ('outfit', 'Outfit Analysis'),
        ('combined', 'Combined Analysis'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='analysis_sessions')
    session_key = models.CharField(max_length=64, db_index=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='face')
    look_name = models.CharField(max_length=120, blank=True)
    summary = models.TextField(blank=True)
    confidence_overall = models.FloatField(default=0.0)
    confidence_data = models.JSONField(default=dict, blank=True)
    raw_ai_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_mode_display()} - {self.look_name or 'Untitled'} ({self.created_at:%Y-%m-%d %H:%M})"


class AnalysisImage(models.Model):
    """Images processed in an analysis session."""
    TYPE_CHOICES = [
        ('face', 'Face Photo'),
        ('outfit', 'Outfit Photo'),
    ]

    session = models.ForeignKey(AnalysisSession, on_delete=models.CASCADE, related_name='images')
    image_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    image_file = models.ImageField(upload_to='analysis/%Y/%m/', null=True, blank=True)
    image_data_uri = models.TextField(blank=True, help_text="Base64 preview data for ephemeral storage")
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    is_validated = models.BooleanField(default=False)
    validation_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session_id} - {self.image_type}"


class FaceAnalysis(models.Model):
    """Structured AI vision extraction for facial features."""
    session = models.OneToOneField(AnalysisSession, on_delete=models.CASCADE, related_name='face_analysis')
    image_quality = models.JSONField(default=dict, blank=True)
    face_visibility = models.JSONField(default=dict, blank=True)
    complexion_observations = models.JSONField(default=dict, blank=True)
    visible_undertone_indicators = models.JSONField(default=dict, blank=True)
    face_shape_estimate = models.JSONField(default=dict, blank=True)
    eye_area = models.JSONField(default=dict, blank=True)
    lip_area = models.JSONField(default=dict, blank=True)
    brow_area = models.JSONField(default=dict, blank=True)
    existing_makeup = models.JSONField(default=dict, blank=True)
    color_harmony = models.JSONField(default=dict, blank=True)
    recommended_makeup_direction = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Face Analysis for {self.session_id}"


class OutfitAnalysis(models.Model):
    """Structured AI vision extraction for clothing/outfit features."""
    session = models.OneToOneField(AnalysisSession, on_delete=models.CASCADE, related_name='outfit_analysis')
    dominant_colors = models.JSONField(default=list, blank=True)
    secondary_colors = models.JSONField(default=list, blank=True)
    pattern = models.CharField(max_length=80, blank=True)
    contrast = models.CharField(max_length=60, blank=True)
    temperature = models.CharField(max_length=60, blank=True)
    saturation = models.CharField(max_length=60, blank=True)
    brightness = models.CharField(max_length=60, blank=True)
    style = models.CharField(max_length=100, blank=True)
    formality = models.CharField(max_length=60, blank=True)
    overall_aesthetic = models.CharField(max_length=120, blank=True)
    raw_details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Outfit Analysis for {self.session_id}"


class MakeupRecommendation(models.Model):
    """Categorical recommendation (Base, Blush, Eyeshadow, Lips, etc.)."""
    session = models.ForeignKey(AnalysisSession, on_delete=models.CASCADE, related_name='recommendations')
    category = models.CharField(max_length=60)
    product_direction = models.CharField(max_length=150)
    color_name = models.CharField(max_length=80, blank=True)
    hex_color = models.CharField(max_length=7, default='#C48D7F')
    temperature = models.CharField(max_length=40, blank=True)
    saturation = models.CharField(max_length=40, blank=True)
    brightness = models.CharField(max_length=40, blank=True)
    finish = models.CharField(max_length=60, blank=True)
    intensity = models.CharField(max_length=60, blank=True)
    placement = models.TextField(blank=True)
    reasoning = models.TextField(blank=True)
    extra_details = models.JSONField(default=dict, blank=True)
    step_order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['step_order']

    def __str__(self):
        return f"{self.category}: {self.product_direction}"


class RecommendedProduct(models.Model):
    """Matching between a recommendation and an actual cosmetic product."""
    recommendation = models.ForeignKey(MakeupRecommendation, on_delete=models.CASCADE, related_name='matched_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    shade = models.ForeignKey(ProductShade, on_delete=models.SET_NULL, null=True, blank=True)
    compatibility_score = models.FloatField(default=0.90)
    role = models.CharField(max_length=100, blank=True, help_text="e.g. Primary Base, Accent Lip")
    usage = models.TextField(blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-compatibility_score']

    def __str__(self):
        return f"{self.product.name} ({self.compatibility_score:.0%})"


class SavedLook(models.Model):
    """User-saved customized makeup look."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='saved_looks')
    session_key = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=140)
    look_name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    mode = models.CharField(max_length=20, default='face')
    routine_data = models.JSONField(default=list, help_text="Ordered steps for the routine")
    visual_summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.created_at:%Y-%m-%d})"


class SavedLookProduct(models.Model):
    """Product assigned to a step in a saved look."""
    saved_look = models.ForeignKey(SavedLook, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    shade = models.ForeignKey(ProductShade, on_delete=models.SET_NULL, null=True, blank=True)
    step_name = models.CharField(max_length=60)
    usage_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.saved_look.title} - {self.step_name}: {self.product.name}"
