import re
import logging
from typing import Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class TextProcessor:
    """Process and normalize text input from clients"""
    
    # Common typos and fixes (русский язык)
    TYPO_MAP = {
        "заити": "зайти",
        "не могу заити": "не могу зайти",
        "кэш": "кеш",
        "кеш": "кеш",
        "ошибка отображ": "ошибка отображения",
    }
    
    # Common keyboard patterns (случайный клавиатурный ввод)
    KEYBOARD_NOISE_PATTERNS = [
        r'^[а-я]{20,}$',  # Long repeated characters
        r'^\d{15,}$',      # Many random numbers
        r'^[a-z]{20,}$',   # Many random Latin chars
    ]
    
    def __init__(self, typo_threshold: float = 0.8):
        """
        Initialize TextProcessor
        
        Args:
            typo_threshold: Similarity threshold for typo correction (0-1)
        """
        self.typo_threshold = typo_threshold
    
    def clean_text(self, text: str) -> str:
        """
        Clean raw text input
        
        Steps:
        1. Strip whitespace
        2. Remove multiple spaces
        3. Remove excessive punctuation
        4. Normalize quotes
        """
        if not text:
            return ""
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive punctuation (!!!  -> !)
        text = re.sub(r'([!?.,;])\1{2,}', r'\1', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"').replace("'", "'")
        
        return text
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text to lowercase for processing
        """
        return text.lower()
    
    def correct_typos(self, text: str) -> str:
        """
        Attempt to correct common typos using fuzzy matching
        
        Strategy:
        1. First try direct replacements from TYPO_MAP
        2. Then use fuzzy matching for longer words
        """
        text_lower = text.lower()
        
        # Direct replacements
        for typo, correction in self.TYPO_MAP.items():
            if typo in text_lower:
                text = text.replace(typo, correction)
                logger.debug(f"Fixed typo: {typo} -> {correction}")
        
        # Fuzzy matching for words
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Skip short words (less than 4 chars)
            if len(word) < 4:
                corrected_words.append(word)
                continue
            
            # Check against typo map values (corrections)
            best_match = None
            best_ratio = 0
            
            for correct_word in set(self.TYPO_MAP.values()):
                ratio = SequenceMatcher(None, word.lower(), correct_word.lower()).ratio()
                if ratio > best_ratio and ratio >= self.typo_threshold:
                    best_ratio = ratio
                    best_match = correct_word
            
            if best_match:
                corrected_words.append(best_match)
                logger.debug(f"Fixed typo (fuzzy): {word} -> {best_match} ({best_ratio:.2f})")
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def remove_noise(self, text: str) -> Optional[str]:
        """
        Detect and remove noise/random input
        Returns None if text is identified as noise
        """
        for pattern in self.KEYBOARD_NOISE_PATTERNS:
            if re.match(pattern, text.lower()):
                logger.warning(f"Detected keyboard noise: {text[:50]}")
                return None
        
        return text
    
    def process(self, text: str) -> str:
        """
        Full pipeline for text processing
        
        Pipeline:
        1. Clean
        2. Detect noise
        3. Correct typos
        4. Normalize
        """
        if not text:
            return ""
        
        # Step 1: Clean
        text = self.clean_text(text)
        
        # Step 2: Remove noise
        text = self.remove_noise(text)
        if text is None:
            return ""
        
        # Step 3: Correct typos
        text = self.correct_typos(text)
        
        # Step 4: Normalize
        text = self.normalize_text(text)
        
        logger.debug(f"Processed text: {text}")
        
        return text
