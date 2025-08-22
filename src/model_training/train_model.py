import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model
import os
import logging

logger = logging.getLogger(__name__)

class FoodModelTrainer:
    def __init__(self):
        self.model = None
        self.input_shape = (224, 224, 3)
        self.batch_size = 32
        self.epochs = 10
        
    def create_model(self):
        """Create and compile the model"""
        base_model = MobileNetV2(
            weights='imagenet',
            include_top=False,
            input_shape=self.input_shape
        )
        
        # Freeze the base model
        base_model.trainable = False
        
        # Add custom layers
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(128, activation='relu')(x)
        predictions = Dense(1, activation='sigmoid')(x)
        
        # Create the model
        self.model = Model(inputs=base_model.input, outputs=predictions)
        
        # Compile the model
        self.model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info("Model created successfully")
        return self.model
    
    def prepare_data(self, data_dir):
        """Prepare data generators"""
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True,
            validation_split=0.2
        )
        
        train_generator = train_datagen.flow_from_directory(
            data_dir,
            target_size=self.input_shape[:2],
            batch_size=self.batch_size,
            class_mode='binary',
            subset='training'
        )
        
        validation_generator = train_datagen.flow_from_directory(
            data_dir,
            target_size=self.input_shape[:2],
            batch_size=self.batch_size,
            class_mode='binary',
            subset='validation'
        )
        
        return train_generator, validation_generator
    
    def train_model(self, train_generator, validation_generator):
        """Train the model"""
        if self.model is None:
            self.create_model()
        
        history = self.model.fit(
            train_generator,
            epochs=self.epochs,
            validation_data=validation_generator
        )
        
        logger.info("Model training completed")
        return history
    
    def save_model(self, model_path):
        """Save the trained model"""
        if self.model is not None:
            self.model.save(model_path)
            logger.info(f"Model saved to {model_path}")
        else:
            logger.error("No model to save")
