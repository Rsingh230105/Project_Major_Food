from django.urls import path, include
from . import views

app_name = 'detector'

urlpatterns = [
    # Main pages
    path('', views.UploadView.as_view(), name='upload'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    
    # Authentication URLs
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # User dashboard and profile
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    
    # API endpoints
    path('api/detect/', views.FoodDetectorView.as_view(), name='detect_food'),
    
    # Media Management URLs (Admin only)
    path('media/ads/', views.AdsUploadView.as_view(), name='upload_ads'),
    path('media/gallery/', views.ProductGalleryView.as_view(), name='gallery'),
    path('media/library/', views.MediaLibraryView.as_view(), name='media_library'),
    path('media/delete/<int:pk>/', views.DeleteMediaView.as_view(), name='delete_media'),
    
    # Django-allauth URLs
    # path('accounts/', include('allauth.urls')),
]
