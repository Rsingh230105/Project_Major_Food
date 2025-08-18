from django.urls import path
from .views import FoodDetectorView, UploadView

app_name = 'detector'

urlpatterns = [
    path('', UploadView.as_view(), name='upload'),  # Upload page at root URL
    path('detect/', FoodDetectorView.as_view(), name='detect_food'),  # API endpoint
]
