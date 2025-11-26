# AI Classifier service - будет реализован в следующем промпте
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

class AIClassifier:
    """Service for classifying customer messages using OpenAI"""
    
    def __init__(self):
        self.settings = get_settings()
        # TODO: Initialize OpenAI client in next prompt
        self.client = None
    
    async def classify(self, text: str) -> dict:
        """
        Classify customer message into scenario type.
        
        Returns:
            {
                "scenario": "GREETING" | "REFERRAL" | "TECH_SUPPORT_BASIC" | "UNKNOWN",
                "confidence": 0.0-1.0,
                "reasoning": "explanation"
            }
        """
        # TODO: Implement OpenAI integration in next prompt
        logger.warning("AIClassifier.classify() not yet implemented")
        return {
            "scenario": "UNKNOWN",
            "confidence": 0.0,
            "reasoning": "Not implemented yet"
        }

