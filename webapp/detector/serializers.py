import io
import logging
from typing import List, Dict, Any, Optional
from rest_framework import serializers
from django.core.files.uploadedfile import InMemoryUploadedFile
from .models import FoodProduct, FoodImage
from .utils.ml_utils import process_product_images

logger = logging.getLogger(__name__)

class FoodImageSerializer(serializers.ModelSerializer):
    """
    Serializer for individual food image views
    """
    view_type_display = serializers.CharField(source='get_view_type_display', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodImage
        fields = ['id', 'image', 'image_url', 'view_type', 'view_type_display', 
                 'uploaded_at', 'prediction', 'confidence', 'detected_text']
        read_only_fields = ['uploaded_at', 'prediction', 'confidence', 'detected_text']
    
    def get_image_url(self, obj: FoodImage) -> Optional[str]:
        """Get the URL for the image if it exists"""
        if obj.image:
            return obj.image.url
        return None

class FoodProductSerializer(serializers.ModelSerializer):
    """
    Serializer for food product with all its images
    """
    images = FoodImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    view_types = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    processing_time = serializers.FloatField(read_only=True)
    brand_match = serializers.BooleanField(read_only=True)
    ocr_results = serializers.DictField(read_only=True)
    
    class Meta:
        model = FoodProduct
        fields = ['id', 'brand_name', 'created_at', 'final_prediction', 
                 'overall_confidence', 'images', 'uploaded_images', 'view_types',
                 'processing_time', 'brand_match', 'ocr_results']
        read_only_fields = ['created_at', 'final_prediction', 'overall_confidence',
                          'processing_time', 'brand_match', 'ocr_results']

    def create(self, validated_data: Dict[str, Any]) -> FoodProduct:
        """
        Create a new FoodProduct instance with multiple images and process them
        """
        # Extract the images and view_types from validated data
        images: List[InMemoryUploadedFile] = validated_data.pop('uploaded_images', [])
        view_types: List[str] = validated_data.pop('view_types', [])

        if len(images) != len(view_types):
            raise serializers.ValidationError(
                "Number of images must match number of view types"
            )

        if not images:
            raise serializers.ValidationError(
                "At least one image is required"
            )

        # Required views validation
        required_views = {'front', 'back'}
        provided_views = set(view_types)
        if not required_views.issubset(provided_views):
            missing = required_views - provided_views
            raise serializers.ValidationError(
                f"Missing required views: {', '.join(missing)}"
            )

        try:
            # Create the food product first
            product = FoodProduct.objects.create(**validated_data)

            # Prepare images for ML processing
            image_dict = {}
            for image, view_type in zip(images, view_types):
                # Read image into memory
                image_bytes = image.read()
                image_dict[view_type] = image_bytes
                
                # Reset file pointer for Django model
                image.seek(0)

            # Process images through ML pipeline
            ml_results = process_product_images(
                images=image_dict,
                brand_name=validated_data['brand_name']
            )

            # Update product with ML results
            product.final_prediction = ml_results['overall_prediction']
            product.overall_confidence = ml_results['overall_confidence']
            product.save()

            # Create FoodImage instances with ML results
            for image, view_type in zip(images, view_types):
                detail = ml_results['detailed_analysis'].get(view_type, {})
                FoodImage.objects.create(
                    product=product,
                    image=image,
                    view_type=view_type,
                    prediction=detail.get('prediction'),
                    confidence=detail.get('confidence'),
                    detected_text=detail.get('ocr_text', '')
                )

            # Store additional ML results
            product.processing_time = ml_results['processing_time']
            product.brand_match = ml_results['brand_match']
            product.ocr_results = ml_results['ocr_results']
            product.save()

            return product

        except Exception as e:
            # If anything fails, delete the product and raise error
            if 'product' in locals():
                product.delete()
            raise serializers.ValidationError(f"Error processing images: {str(e)}")

    def to_representation(self, instance: FoodProduct) -> Dict[str, Any]:
        """
        Customize the output representation of the serializer
        """
        try:
            data = super().to_representation(instance)
            
            # Ensure all fields have default values
            data.setdefault('brand_name', '')
            data.setdefault('final_prediction', 'Unknown')
            data.setdefault('overall_confidence', 0.0)
            data.setdefault('processing_time', 0.0)
            data.setdefault('brand_match', False)
            data.setdefault('ocr_results', {})
            data.setdefault('images', [])
            
            # Add a flag to indicate if all required views are present
            required_views = {'front', 'back'}
            uploaded_views = {img['view_type'] for img in data['images']}
            data['has_required_views'] = required_views.issubset(uploaded_views)
            
            # Format values for frontend display
            if data['overall_confidence']:
                data['overall_confidence'] = round(float(data['overall_confidence']) * 100, 1)
            
            if data['processing_time']:
                data['processing_time'] = round(float(data['processing_time']), 2)
            
            # Format image results
            for img in data['images']:
                if img.get('confidence'):
                    img['confidence'] = round(float(img['confidence']) * 100, 1)

            return data
            
        except Exception as e:
            logger.error(f"Error in serializer representation: {e}")
            # Return minimal valid response in case of error
            return {
                'brand_name': instance.brand_name,
                'error': 'Error processing results'
            }
