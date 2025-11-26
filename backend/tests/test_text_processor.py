import pytest
from app.services.text_processor import TextProcessor

@pytest.fixture
def processor():
    return TextProcessor()

def test_clean_text_whitespace(processor):
    """Test whitespace cleaning"""
    assert processor.clean_text("  hello  world  ") == "hello world"
    assert processor.clean_text("\t\nhello\r\n") == "hello"

def test_clean_text_punctuation(processor):
    """Test excessive punctuation removal"""
    assert processor.clean_text("hello!!!") == "hello!"
    assert processor.clean_text("what???") == "what?"
    assert processor.clean_text("ok...") == "ok."

def test_normalize_text(processor):
    """Test text normalization"""
    assert processor.normalize_text("HELLO") == "hello"
    assert processor.normalize_text("ПривЕт") == "привет"

def test_correct_typos(processor):
    """Test typo correction"""
    result = processor.correct_typos("не могу заити")
    assert "зайти" in result.lower()

def test_remove_noise(processor):
    """Test noise detection"""
    # Random characters should be detected as noise
    result = processor.remove_noise("aaaaaaaaaaaaaaaaaaaaaaa")
    assert result is None
    
    # Normal text should pass through
    result = processor.remove_noise("hello world")
    assert result == "hello world"

def test_process_pipeline(processor):
    """Test full processing pipeline"""
    text = "  НЕ МОГУ ЗАИТИ В КАБИНЕТ!!!  "
    result = processor.process(text)
    
    assert isinstance(result, str)
    assert len(result) > 0
    assert result.islower()
    assert "!!!" not in result
