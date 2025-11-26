# Response Manager service - будет реализован в следующем промпте
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

class ResponseManager:
    """Service for selecting and formatting response templates"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def get_template(self, scenario: str) -> str:
        """
        Get response template for scenario.
        
        Args:
            scenario: Scenario type (GREETING, REFERRAL, etc.)
            
        Returns:
            Template text
        """
        # TODO: Implement template selection from DB in next prompt
        logger.warning("ResponseManager.get_template() not yet implemented")
        return "Template not implemented yet"
    
    async def format_response(self, template: str, params: dict = None) -> str:
        """
        Format template with parameters.
        
        Args:
            template: Template text
            params: Parameters to fill in
            
        Returns:
            Formatted response
        """
        if not params:
            return template
        
        # Simple string formatting
        try:
            return template.format(**params)
        except KeyError as e:
            logger.error(f"Missing parameter in template: {e}")
            return template

