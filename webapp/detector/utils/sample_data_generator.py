import random
import json
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

class SampleDataGenerator:
    """
    Generate sample data for development and testing
    """
    def __init__(self):
        self.brands = ['Maggi', 'Parle-G', 'Britannia', 'Haldiram']
        self.output_dir = Path(__file__).parent.parent.parent / 'media' / 'sample_data'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_sample_image(self, brand_name, is_real=True, view_type='front'):
        """Generate a sample image with text"""
        # Create a new image with a white background
        img = Image.new('RGB', (800, 800), color='white')
        d = ImageDraw.Draw(img)
        
        # Add sample text
        text = f"{brand_name}\n{'REAL' if is_real else 'FAKE'}\n{view_type.upper()} VIEW"
        d.text((400, 400), text, fill='black', anchor="mm")
        
        # Create filename
        status = 'real' if is_real else 'fake'
        filename = f"{brand_name.lower()}_{status}_{view_type}.jpg"
        filepath = self.output_dir / filename
        
        # Save image
        img.save(filepath)
        return filepath

    def generate_sample_result(self, brand_name):
        """Generate sample analysis result"""
        is_real = random.choice([True, False])
        confidence = random.uniform(0.7, 0.99)
        
        return {
            'brand_name': brand_name,
            'is_real': is_real,
            'confidence': confidence,
            'ocr_text': f"Sample OCR text for {brand_name}",
            'detected_features': {
                'logo_detected': random.choice([True, False]),
                'barcode_valid': random.choice([True, False]),
                'text_quality': random.uniform(0.6, 1.0)
            }
        }

    def generate_sample_dataset(self, num_samples=5):
        """Generate multiple sample images and results"""
        dataset = []
        
        for _ in range(num_samples):
            brand = random.choice(self.brands)
            is_real = random.choice([True, False])
            
            # Generate images for different views
            images = {}
            for view in ['front', 'back', 'side', 'barcode']:
                filepath = self.generate_sample_image(brand, is_real, view)
                images[view] = str(filepath)
            
            # Generate analysis result
            result = self.generate_sample_result(brand)
            result['images'] = images
            dataset.append(result)
        
        # Save results to JSON file
        results_file = self.output_dir / 'sample_results.json'
        with open(results_file, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        return dataset

if __name__ == '__main__':
    generator = SampleDataGenerator()
    samples = generator.generate_sample_dataset(5)
    print(f"Generated {len(samples)} sample entries")
