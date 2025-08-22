from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.generic import TemplateView
from django.shortcuts import render
import logging
from .serializers import FoodProductSerializer, FoodImageSerializer
from .models import FoodProduct, FoodImage

logger = logging.getLogger(__name__)

class UploadView(TemplateView):
    """
    View for the image upload page
    """
    template_name = 'detector/upload.html'

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class FoodDetectorView(APIView):
    """
    API endpoint for food detection
    """
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests - provides API documentation
        """
        return Response({
            'message': 'Welcome to the Food Detection API',
            'endpoints': {
                'POST /api/detect/': {
                    'description': 'Detect fake/real food from multiple images',
                    'parameters': {
                        'brand_name': 'Name of the food product',
                        'images': 'Multiple image files (JPEG/PNG)',
                        'view_types': 'Type of view for each image (front, back, side, barcode, other)'
                    },
                    'returns': {
                        'final_prediction': 'Overall Real/Fake classification',
                        'overall_confidence': 'Combined confidence score (0-1)',
                        'images': 'Analysis results for each uploaded image'
                    }
                }
            },
            'supported_formats': ['image/jpeg', 'image/png'],
            'max_file_size': '5MB per image',
            'required_views': ['front', 'back']
        }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for food detection with multiple images
        """
        try:
            # Log request data for debugging
            logger.info(f"Received request data: {request.data}")
            logger.info(f"Files: {request.FILES}")
            
            # Extract data from request
            brand_name = request.POST.get('brand_name')
            images = request.FILES.getlist('images[]')
            view_types = request.POST.getlist('view_types[]')
            
            logger.info(f"Brand name: {brand_name}")
            logger.info(f"Number of images: {len(images)}")
            logger.info(f"View types: {view_types}")
            
            # Validate required fields
            if not brand_name:
                logger.warning("Brand name missing in request")
                return Response({
                    'error': 'Brand name is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not images:
                logger.warning("No images found in request")
                return Response({
                    'error': 'At least one image is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            if len(images) != len(view_types):
                logger.warning(f"Mismatch in number of images ({len(images)}) and view types ({len(view_types)})")
                return Response({
                    'error': 'Number of images and view types must match'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create product with nested images
            serializer = FoodProductSerializer(data={
                'brand_name': brand_name,
                'uploaded_images': images,
                'view_types': view_types
            })

            if serializer.is_valid():
                product = serializer.save()

                # TODO: Integrate ML model predictions here
                # For now, simulate predictions
                from random import random, choice
                predictions = ['Real', 'Fake']

                # Update predictions for each image
                overall_confidence = 0
                predictions_count = {'Real': 0, 'Fake': 0}

                for image in product.images.all():
                    # Simulate ML prediction for each image
                    pred = choice(predictions)
                    conf = random() * 0.5 + 0.5  # Random confidence between 0.5 and 1.0
                    
                    # Update image prediction
                    image.prediction = pred
                    image.confidence = conf
                    image.detected_text = f"Sample text for {image.get_view_type_display()}"
                    image.save()

                    # Track overall predictions
                    predictions_count[pred] += 1
                    overall_confidence += conf

                # Calculate final prediction and overall confidence
                total_images = len(product.images.all())
                final_pred = 'Real' if predictions_count['Real'] > predictions_count['Fake'] else 'Fake'
                overall_conf = overall_confidence / total_images if total_images > 0 else 0

                # Update product with final results
                product.final_prediction = final_pred
                product.overall_confidence = overall_conf
                product.save()

                # Return updated product data
                return Response(
                    FoodProductSerializer(product).data,
                    status=status.HTTP_201_CREATED
                )
            
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Error processing food detection request: {str(e)}")
            return Response(
                {'error': 'Internal server error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


