import pytest
from app.services.text_processor import TextProcessor

def test_clean_text():
    """Test text cleaning"""
    processor = TextProcessor()
    
    # Test case 1: Простой текст
    result = processor.clean_text("  Привет мир  ")
    assert result == "Привет мир"
    
    # Test case 2: Опечатки
    result = processor.clean_text("не могу заити")
    # TODO: implement fuzzy matching
    
    # Test case 3: Спецсимволы
    result = processor.clean_text("Hello!!! How are you???")
    assert "!!!" not in result or result.count("!") <= 1

def test_normalize_text():
    """Test text normalization"""
    processor = TextProcessor()
    
    result = processor.normalize_text("ПРИВЕТ")
    assert result.islower()

