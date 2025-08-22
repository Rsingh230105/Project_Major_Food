import os
from train_model import FoodModelTrainer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Initialize paths
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'training_data')
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'mobilenet_v2_food.h5')
    
    # Create trainer instance
    trainer = FoodModelTrainer()
    
    try:
        # Prepare data
        logger.info("Preparing data generators...")
        train_generator, validation_generator = trainer.prepare_data(data_dir)
        
        # Create and train model
        logger.info("Starting model training...")
        trainer.create_model()
        history = trainer.train_model(train_generator, validation_generator)
        
        # Save model
        logger.info("Saving trained model...")
        trainer.save_model(model_path)
        
        logger.info("Training completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during training: {str(e)}")
        raise

if __name__ == "__main__":
    main()
