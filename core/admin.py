from django.contrib import admin
from .models import (
    UserProfile, ProductBrand, ProductCategory, Product, ProductShade,
    UserProduct, AnalysisSession, AnalysisImage, FaceAnalysis, OutfitAnalysis,
    MakeupRecommendation, RecommendedProduct, SavedLook, SavedLookProduct
)


@admin.register(ProductBrand)
class ProductBrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'website']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


class ProductShadeInline(admin.TabularInline):
    model = ProductShade
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'finish', 'price', 'is_active']
    list_filter = ['brand', 'category', 'finish', 'is_active']
    search_fields = ['name', 'brand__name', 'category__name']
    inlines = [ProductShadeInline]


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'step_order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(UserProduct)
class UserProductAdmin(admin.ModelAdmin):
    list_display = ['product', 'shade', 'session_key', 'is_in_makeup_bag', 'created_at']
    list_filter = ['is_in_makeup_bag']
    search_fields = ['product__name', 'session_key']


@admin.register(AnalysisSession)
class AnalysisSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'mode', 'look_name', 'confidence_overall', 'session_key', 'created_at']
    list_filter = ['mode', 'created_at']
    search_fields = ['look_name', 'session_key']


@admin.register(SavedLook)
class SavedLookAdmin(admin.ModelAdmin):
    list_display = ['title', 'look_name', 'session_key', 'created_at']
    search_fields = ['title', 'look_name', 'session_key']
