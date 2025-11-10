from rest_framework import serializers
from .models import CustomUser, FoodProduct, FoodImage, UserProfile

class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for custom user model"""
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 
                 'phone_number', 'profile_picture', 'is_email_verified', 'created_at']
        read_only_fields = ['id', 'is_email_verified', 'created_at']

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    user = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['user', 'bio', 'location', 'birth_date', 'website', 
                 'profile_visibility', 'email_notifications', 'sms_notifications']

class FoodImageSerializer(serializers.ModelSerializer):
    """Serializer for food images"""
    class Meta:
        model = FoodImage
        fields = ['id', 'image', 'view_type', 'prediction', 'confidence', 
                 'detected_text', 'uploaded_at', 'file_size', 'image_width', 'image_height']
        read_only_fields = ['id', 'uploaded_at', 'file_size', 'image_width', 'image_height']

class FoodProductSerializer(serializers.ModelSerializer):
    """Serializer for food products"""
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
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = FoodProduct
        fields = ['id', 'user', 'brand_name', 'final_prediction', 'overall_confidence',
                 'processing_time', 'brand_match', 'ocr_results', 'risk_level',
                 'analysis_notes', 'created_at', 'images', 'uploaded_images', 'view_types']
        read_only_fields = ['id', 'created_at', 'final_prediction', 'overall_confidence',
                           'processing_time', 'brand_match', 'ocr_results']

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        view_types = validated_data.pop('view_types', [])
        
        # Create the product
        product = FoodProduct.objects.create(**validated_data)
        
        # Create associated images
        for i, image in enumerate(uploaded_images):
            view_type = view_types[i] if i < len(view_types) else 'other'
            FoodImage.objects.create(
                product=product,
                image=image,
                view_type=view_type
            )
        
        return product

class FoodProductListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing food products"""
    images_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodProduct
        fields = ['id', 'brand_name', 'final_prediction', 'overall_confidence',
                 'risk_level', 'created_at', 'images_count']
    
    def get_images_count(self, obj):
        return obj.images.count()