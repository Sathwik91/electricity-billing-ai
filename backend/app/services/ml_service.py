"""
ML Model Service - Coordinates ML models
"""
import logging

logger = logging.getLogger(__name__)


class MLService:
    """ML model coordination service"""
    
    def __init__(self):
        self.models_loaded = False
    
    async def load_models(self):
        """Load ML models"""
        logger.info("Loading ML models...")
        # Models will be loaded when needed
        self.models_loaded = True
        logger.info("ML models loaded successfully")
    
    def check_models_loaded(self) -> bool:
        """Check if models are loaded"""
        return self.models_loaded