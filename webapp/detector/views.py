"""Detector app views with complete authentication system."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
import logging

from .models import (CustomUser, UserProfile, FoodProduct, FoodImage, 
                    Advertisement, GalleryItem, MediaItem, UserActivity)
from .forms import CustomUserRegistrationForm, CustomUserLoginForm, UserProfileForm, CustomUserUpdateForm
from .serializers import FoodProductSerializer, FoodImageSerializer

logger = logging.getLogger(__name__)

def log_user_activity(user, activity_type, description="", request=None):
    """Helper function to log user activities"""
    if user and user.is_authenticated:
        ip_address = None
        user_agent = ""
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )

class UploadView(TemplateView):
    """View for the image upload page"""
    template_name = 'detector/upload.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get active advertisements
        context['advertisements'] = Advertisement.objects.filter(is_active=True).order_by('-created_at')[:5]
        return context

class AboutView(TemplateView):
    template_name = 'detector/about.html'

class HomeView(TemplateView):
    template_name = 'detector/home.html'

class ContactView(TemplateView):
    template_name = 'detector/contact.html'

    def post(self, request, *args, **kwargs):
        # Handle contact form submission
        return redirect('detector:upload')

class RegisterView(View):
    """User registration view"""
    template_name = 'auth/register.html'
    form_class = CustomUserRegistrationForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('detector:dashboard')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('detector:dashboard')
        
        form = self.form_class(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    # Log registration activity
                    log_user_activity(user, 'register', 'User registered successfully', request)
                    
                    messages.success(request, 'Registration successful! Please check your email to verify your account.')
                    return redirect('detector:login')
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                messages.error(request, 'Registration failed. Please try again.')
        
        return render(request, self.template_name, {'form': form})

class LoginView(View):
    """User login view"""
    template_name = 'auth/login.html'
    form_class = CustomUserLoginForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('detector:dashboard')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('detector:dashboard')
        
        form = self.form_class(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Log login activity
            log_user_activity(user, 'login', 'User logged in successfully', request)
            
            messages.success(request, f'Welcome back, {user.first_name}!')
            
            # Redirect to next page or dashboard
            next_page = request.GET.get('next', 'detector:dashboard')
            return redirect(next_page)
        
        return render(request, self.template_name, {'form': form})

class DashboardView(LoginRequiredMixin, TemplateView):
    """User dashboard view"""
    template_name = 'detector/dashboard.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's recent food products
        recent_products = FoodProduct.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Get user statistics
        total_analyses = FoodProduct.objects.filter(user=user).count()
        fake_products = FoodProduct.objects.filter(user=user, final_prediction='Fake').count()
        real_products = FoodProduct.objects.filter(user=user, final_prediction='Real').count()
        
        # Get recent activities
        recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:10]
        
        context.update({
            'recent_products': recent_products,
            'total_analyses': total_analyses,
            'fake_products': fake_products,
            'real_products': real_products,
            'recent_activities': recent_activities,
        })
        return context

class ProfileView(LoginRequiredMixin, View):
    """User profile view"""
    template_name = 'detector/profile.html'
    login_url = '/login/'

    def get(self, request):
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        user_form = CustomUserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
        
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        user_form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    user_form.save()
                    profile_form.save()
                    
                    # Log profile update activity
                    log_user_activity(user, 'profile_update', 'Profile updated successfully', request)
                    
                    messages.success(request, 'Profile updated successfully!')
                    return redirect('detector:profile')
            except Exception as e:
                logger.error(f"Profile update error: {str(e)}")
                messages.error(request, 'Profile update failed. Please try again.')
        
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile,
        }
        return render(request, self.template_name, context)

class AnalysesView(LoginRequiredMixin, TemplateView):
    """View for displaying user's analysis history with search and pagination"""
    template_name = 'detector/analyses.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get search query
        search_query = self.request.GET.get('search', '')
        
        # Get all user's products
        products = FoodProduct.objects.filter(user=user).order_by('-created_at')
        
        if search_query:
            products = products.filter(
                Q(brand_name__icontains=search_query) |
                Q(final_prediction__icontains=search_query) |
                Q(analysis_notes__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(products, 10)  # 10 items per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context.update({
            'products': page_obj,
            'search_query': search_query,
            'total_analyses': products.count(),
        })
        return context

class SettingsView(LoginRequiredMixin, TemplateView):
    """User settings view"""
    template_name = 'detector/settings.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        context['profile'] = profile
        return context

@login_required
def logout_view(request):
    """User logout view"""
    user = request.user
    log_user_activity(user, 'logout', 'User logged out', request)
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('detector:upload')

# Media Management Views (Admin only)
class AdsUploadView(UserPassesTestMixin, TemplateView):
    """View for uploading advertisements and awareness content"""
    template_name = 'detector/media/ads_upload.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['advertisements'] = Advertisement.objects.all().order_by('-created_at')
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('detector:upload')

        try:
            files = request.FILES.getlist('files')
            content_type = request.POST.get('content_type')
            title = request.POST.get('title')
            description = request.POST.get('description')
            duration = request.POST.get('duration')

            for file in files:
                Advertisement.objects.create(
                    title=title,
                    description=description,
                    file=file,
                    content_type=content_type,
                    duration_days=int(duration) if duration else 30,
                    uploaded_by=request.user
                )
            messages.success(request, "Advertisement uploaded successfully")
            return redirect('detector:upload_ads')
        except Exception as e:
            messages.error(request, f"Error uploading advertisement: {str(e)}")
            return self.get(request, *args, **kwargs)

class ProductGalleryView(UserPassesTestMixin, TemplateView):
    """View for managing product comparison gallery"""
    template_name = 'detector/media/gallery.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = [
            'Real vs Fake Comparisons',
            'Packaging Verification',
            'Safety Guidelines'
        ]
        # Show only approved items to non-staff, all items to staff
        if self.request.user.is_staff:
            context['gallery_items'] = GalleryItem.objects.all().order_by('-created_at')
        else:
            context['gallery_items'] = GalleryItem.objects.filter(status='approved').order_by('-created_at')
        return context

    def post(self, request, *args, **kwargs):
        try:
            files = request.FILES.getlist('images')
            title = request.POST.get('title')
            category = request.POST.get('category')
            description = request.POST.get('description', '')

            for file in files:
                # Admin uploads are auto-approved, user uploads need approval
                status = 'approved' if request.user.is_staff else 'pending'
                GalleryItem.objects.create(
                    title=title,
                    description=description,
                    category=category,
                    image=file,
                    status=status,
                    uploaded_by=request.user,
                    approved_by=request.user if request.user.is_staff else None,
                    approved_at=timezone.now() if request.user.is_staff else None
                )
            
            if request.user.is_staff:
                messages.success(request, "Gallery items uploaded and approved successfully")
            else:
                messages.success(request, "Gallery items uploaded! Waiting for admin approval.")
            return redirect('detector:gallery')
        except Exception as e:
            messages.error(request, f"Error uploading gallery items: {str(e)}")
            return self.get(request, *args, **kwargs)

class MediaLibraryView(TemplateView):
    """View for browsing all media content"""
    template_name = 'detector/media/library.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Show only approved items to non-staff
        if self.request.user.is_authenticated and self.request.user.is_staff:
            media_items = MediaItem.objects.all().order_by('-created_at')
        else:
            media_items = MediaItem.objects.filter(status='approved').order_by('-created_at')
        
        # Pagination
        paginator = Paginator(media_items, 12)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['media_items'] = page_obj
        return context

class DeleteMediaView(UserPassesTestMixin, View):
    """View for deleting media items"""

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, pk):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        for model in (Advertisement, GalleryItem, MediaItem):
            try:
                obj = model.objects.get(pk=pk)
                obj.delete()
                return JsonResponse({'status': 'success'})
            except model.DoesNotExist:
                continue

        return JsonResponse({'error': 'Not found'}, status=404)

# API Views
class FoodDetectorView(APIView):
    """API endpoint for food detection"""
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
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
        try:
            logger.info(f"Received request data: {request.data}")
            logger.info(f"Files: {request.FILES}")

            brand_name = request.POST.get('brand_name')
            images = request.FILES.getlist('images[]')
            view_types = request.POST.getlist('view_types[]')

            if not brand_name:
                return Response({'error': 'Brand name is required'}, status=status.HTTP_400_BAD_REQUEST)

            if not images:
                return Response({'error': 'At least one image is required'}, status=status.HTTP_400_BAD_REQUEST)

            if len(images) != len(view_types):
                return Response({'error': 'Number of images and view types must match'}, status=status.HTTP_400_BAD_REQUEST)

            # Create product with user association if authenticated
            user = request.user if request.user.is_authenticated else None
            
            serializer = FoodProductSerializer(data={
                'brand_name': brand_name,
                'uploaded_images': images,
                'view_types': view_types,
                'user': user.id if user else None
            })

            if serializer.is_valid():
                product = serializer.save()
                
                # Log analysis activity
                if user:
                    log_user_activity(user, 'analysis', f'Analyzed product: {brand_name}', request)

                # Simulate ML processing (replace with actual ML logic)
                from random import random, choice
                predictions = ['Real', 'Fake']

                overall_confidence = 0
                predictions_count = {'Real': 0, 'Fake': 0}

                for image in product.images.all():
                    pred = choice(predictions)
                    conf = random() * 0.5 + 0.5
                    image.prediction = pred
                    image.confidence = conf
                    image.detected_text = f"Sample text for {image.get_view_type_display()}"
                    image.save()

                    predictions_count[pred] += 1
                    overall_confidence += conf

                total_images = len(product.images.all())
                final_pred = 'Real' if predictions_count['Real'] > predictions_count['Fake'] else 'Fake'
                overall_conf = overall_confidence / total_images if total_images > 0 else 0

                product.final_prediction = final_pred
                product.overall_confidence = overall_conf
                product.save()

                return Response(FoodProductSerializer(product).data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error processing food detection request: {str(e)}")
            return Response({'error': 'Internal server error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)