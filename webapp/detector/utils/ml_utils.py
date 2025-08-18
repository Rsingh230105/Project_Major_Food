from typing import Dict, List, Tuple, Optional, Union
import numpy as np
import tensorflow as tf
import cv2
import pytesseract
from PIL import Image
import logging
from pathlib import Path
import re
from datetime import datetime
from fuzzywuzzy import fuzz
import io

logger = logging.getLogger(__name__)

class MLPredictor:
    """
    Handles ML model loading and inference for food product authenticity detection
    """
    def __init__(self):
        self.model = None
        self.model_path = Path(__file__).parent.parent.parent.parent / 'models' / 'mobilenet_v2_food.h5'
        self.target_size = (224, 224)
        self.class_names = ['FAKE', 'REAL']
        self._load_model()

    def _load_model(self) -> None:
        """
        Load the MobileNetV2 model on first use.
        During development, if model is not found, use a dummy model.
        """
        try:
            if self.model is None:
                if self.model_path.exists():
                    self.model = tf.keras.models.load_model(str(self.model_path))
                    logger.info("ML model loaded successfully")
                else:
                    # For development: Create a dummy model that returns random predictions
                    logger.warning(f"Model not found at {self.model_path}, using dummy model for development")
                    inputs = tf.keras.Input(shape=(224, 224, 3))
                    x = tf.keras.layers.GlobalAveragePooling2D()(inputs)
                    outputs = tf.keras.layers.Dense(1, activation='sigmoid')(x)
                    self.model = tf.keras.Model(inputs=inputs, outputs=outputs)
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
            raise

    def preprocess_image(self, image_data: Union[bytes, np.ndarray]) -> np.ndarray:
        """
        Preprocess image for model inference
        
        Args:
            image_data: Raw image bytes or numpy array
            
        Returns:
            Preprocessed image array normalized to [0,1]
        """
        try:
            # Convert bytes to numpy array if needed
            if isinstance(image_data, bytes):
                nparr = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                img = image_data

            # Convert BGR to RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Resize with aspect ratio preservation
            h, w = img.shape[:2]
            if h > w:
                new_h = int(self.target_size[0] * (h/w))
                img = cv2.resize(img, (self.target_size[0], new_h))
            else:
                new_w = int(self.target_size[1] * (w/h))
                img = cv2.resize(img, (new_w, self.target_size[1]))
            
            # Center crop
            h, w = img.shape[:2]
            start_h = (h - self.target_size[0]) // 2
            start_w = (w - self.target_size[1]) // 2
            img = img[start_h:start_h + self.target_size[0], 
                     start_w:start_w + self.target_size[1]]
            
            # Normalize to [0,1]
            img = img.astype(np.float32) / 255.0
            
            # Add batch dimension
            img = np.expand_dims(img, axis=0)
            
            return img
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise ValueError(f"Image preprocessing failed: {e}")

    def predict_single(self, image_data: Union[bytes, np.ndarray]) -> Tuple[str, float]:
        """
        Make prediction on a single image
        
        Args:
            image_data: Raw image bytes or numpy array
            
        Returns:
            Tuple of (prediction label, confidence score)
        """
        try:
            # Ensure model is loaded
            if self.model is None:
                self._load_model()
            
            # Preprocess image
            processed_img = self.preprocess_image(image_data)
            
            # Get prediction
            pred = self.model.predict(processed_img, verbose=0)[0]
            
            # Get class and confidence
            pred_class = self.class_names[int(round(pred[0]))]
            confidence = float(pred[0]) if pred_class == 'REAL' else float(1 - pred[0])
            
            return pred_class, confidence
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

class OCRProcessor:
    """
    Handles OCR processing and text extraction from images
    """
    def __init__(self):
        self.date_pattern = r'(\d{2}\/\d{2}\/\d{4}|\d{2}\.\d{2}\.\d{4})'
        self.batch_pattern = r'batch\s*(?:no\.?|number\.?)?\s*:?\s*([a-z0-9]+)'
        self.mrp_pattern = r'mrp\.?\s*:?\s*(?:rs\.?)?\s*(\d+(?:\.\d{2})?)'

    def process_image(self, image_data: Union[bytes, np.ndarray]) -> Dict[str, str]:
        """
        Extract text and key information from image
        
        Args:
            image_data: Raw image bytes or numpy array
            
        Returns:
            Dict containing extracted text and structured information
        """
        try:
            # Convert bytes to PIL Image
            if isinstance(image_data, bytes):
                img = Image.open(io.BytesIO(image_data))
            else:
                img = Image.fromarray(cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB))

            # Extract text using Tesseract
            text = pytesseract.image_to_string(img)
            text = text.lower()

            # Extract structured information
            result = {
                'full_text': text,
                'expiry_date': self._extract_date(text),
                'batch_number': self._extract_batch(text),
                'mrp': self._extract_mrp(text),
                'extracted_brands': self._extract_brands(text)
            }

            return result

        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract expiry/manufacturing date"""
        match = re.search(self.date_pattern, text)
        return match.group(1) if match else None

    def _extract_batch(self, text: str) -> Optional[str]:
        """Extract batch number"""
        match = re.search(self.batch_pattern, text, re.I)
        return match.group(1).upper() if match else None

    def _extract_mrp(self, text: str) -> Optional[str]:
        """Extract MRP"""
        match = re.search(self.mrp_pattern, text, re.I)
        return match.group(1) if match else None

    def _extract_brands(self, text: str) -> List[str]:
        """
        Extract potential brand names from text
        Uses common Indian FMCG brand names
        """
        common_brands = ['maggi', 'nestle', 'amul', 'parle', 'britannia', 'haldirams', 
                        'mtr', 'patanjali', 'itc', 'dabur', 'mother dairy']
        found_brands = []
        
        for brand in common_brands:
            if brand in text.lower():
                found_brands.append(brand.upper())
        
        return found_brands

    def verify_brand(self, ocr_brands: List[str], user_brand: str, threshold: int = 80) -> bool:
        """
        Verify if OCR extracted brands match user provided brand
        Uses fuzzy string matching to handle minor variations
        """
        if not ocr_brands:
            return False
            
        user_brand = user_brand.lower()
        for brand in ocr_brands:
            if fuzz.ratio(brand.lower(), user_brand) >= threshold:
                return True
                
        return False

# Singleton instances for reuse
ml_predictor = MLPredictor()
ocr_processor = OCRProcessor()

def process_product_images(
    images: Dict[str, bytes], 
    brand_name: str
) -> Dict[str, Union[str, float, Dict]]:
    """
    Process multiple product images and combine results
    
    Args:
        images: Dict of image type to image data
        brand_name: User provided brand name
        
    Returns:
        Dict containing combined analysis results
    """
    try:
        results = {
            'overall_prediction': None,
            'overall_confidence': 0.0,
            'brand_match': False,
            'detailed_analysis': {},
            'ocr_results': {
                'extracted_brands': set(),
                'expiry_dates': set(),
                'batch_numbers': set(),
                'mrp_values': set()
            },
            'processing_time': 0.0
        }
        
        start_time = datetime.now()
        total_confidence = 0.0
        predictions = {'REAL': 0, 'FAKE': 0}
        
        # Process each image
        for view_type, image_data in images.items():
            # ML prediction
            pred_class, confidence = ml_predictor.predict_single(image_data)
            predictions[pred_class] += 1
            total_confidence += confidence
            
            # OCR processing
            ocr_result = ocr_processor.process_image(image_data)
            
            # Store detailed results
            results['detailed_analysis'][view_type] = {
                'prediction': pred_class,
                'confidence': confidence,
                'ocr_text': ocr_result['full_text']
            }
            
            # Aggregate OCR results
            if ocr_result['extracted_brands']:
                results['ocr_results']['extracted_brands'].update(ocr_result['extracted_brands'])
            if ocr_result['expiry_date']:
                results['ocr_results']['expiry_dates'].add(ocr_result['expiry_date'])
            if ocr_result['batch_number']:
                results['ocr_results']['batch_numbers'].add(ocr_result['batch_number'])
            if ocr_result['mrp']:
                results['ocr_results']['mrp_values'].add(ocr_result['mrp'])
        
        # Calculate overall results
        num_images = len(images)
        results['overall_prediction'] = 'REAL' if predictions['REAL'] > predictions['FAKE'] else 'FAKE'
        results['overall_confidence'] = total_confidence / num_images if num_images > 0 else 0.0
        
        # Convert sets to lists for JSON serialization
        results['ocr_results'] = {k: list(v) for k, v in results['ocr_results'].items()}
        
        # Check brand match
        results['brand_match'] = ocr_processor.verify_brand(
            results['ocr_results']['extracted_brands'], 
            brand_name
        )
        
        # Calculate processing time
        results['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing product images: {e}")
        raise
