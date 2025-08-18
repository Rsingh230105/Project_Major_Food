from django.db import models

class FoodProduct(models.Model):
    """
    Model for storing food product analysis with ML and OCR results
    """
    brand_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    final_prediction = models.CharField(max_length=10, blank=True)  # 'REAL' or 'FAKE'
    overall_confidence = models.FloatField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # Processing time in seconds
    brand_match = models.BooleanField(default=False)  # Whether OCR found matching brand
    ocr_results = models.JSONField(default=dict, blank=True)  # Structured OCR results

    def __str__(self):
        return f"{self.brand_name} Analysis - {self.final_prediction}"

class FoodImage(models.Model):
    """
    Model for storing multiple views of food product images
    """
    VIEWS = [
        ('front', 'Front View'),
        ('back', 'Back View'),
        ('side', 'Side View'),
        ('barcode', 'Barcode/QR'),
        ('other', 'Other View')
    ]

    product = models.ForeignKey(FoodProduct, on_delete=models.CASCADE, related_name='images', null=True)
    image = models.ImageField(upload_to='food_images/')
    view_type = models.CharField(max_length=10, choices=VIEWS, default='front')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    prediction = models.CharField(max_length=10, blank=True)  # Individual prediction for this view
    confidence = models.FloatField(null=True, blank=True)
    detected_text = models.TextField(blank=True)  # Text extracted from this view

    class Meta:
        ordering = ['view_type']

    def __str__(self):
        return f"{self.product.brand_name} - {self.get_view_type_display()}"
