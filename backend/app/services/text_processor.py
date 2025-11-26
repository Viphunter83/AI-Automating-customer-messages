import re
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    """Service for cleaning and normalizing text"""
    
    def clean_text(self, text: str) -> str:
        """
        Clean text: remove extra spaces, normalize punctuation.
        
        Args:
            text: Raw input text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize multiple punctuation marks
        text = re.sub(r'!{2,}', '!', text)
        text = re.sub(r'\?{2,}', '?', text)
        text = re.sub(r'\.{2,}', '.', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text: lowercase, remove accents (future).
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # TODO: Add fuzzy matching for typos in next prompt
        
        return text
    
    def extract_keywords(self, text: str) -> list[str]:
        """
        Extract keywords from text (simple version).
        
        Args:
            text: Input text
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction - will be enhanced later
        words = re.findall(r'\b[а-яёa-z]{3,}\b', text.lower())
        return list(set(words))

