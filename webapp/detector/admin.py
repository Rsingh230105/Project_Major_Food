from django.contrib import admin
from .models import FoodProduct, FoodImage

@admin.register(FoodImage)
class FoodImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'view_type', 'prediction', 'confidence', 'uploaded_at']
    list_filter = ['view_type', 'prediction', 'uploaded_at']
    search_fields = ['product__brand_name', 'detected_text']
    readonly_fields = ['uploaded_at']

@admin.register(FoodProduct)
class FoodProductAdmin(admin.ModelAdmin):
    list_display = ['brand_name', 'final_prediction', 'overall_confidence', 'created_at']
    list_filter = ['final_prediction', 'brand_match', 'created_at']
    search_fields = ['brand_name']
    readonly_fields = ['created_at', 'processing_time']
