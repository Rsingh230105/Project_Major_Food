from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

class FoodDetectorTests(APITestCase):
    def setUp(self):
        self.url = reverse('detector:detect_food')

    def test_get_endpoint(self):
        """
        Ensure we can get API documentation
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('endpoints', response.data)
        self.assertIn('supported_formats', response.data)

    def test_post_endpoint(self):
        """
        Ensure we can access the food detection endpoint
        """
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('status', response.data)
        self.assertIn('supported_formats', response.data)
