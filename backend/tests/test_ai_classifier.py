import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.ai_classifier import AIClassifier
import json

@pytest.fixture
def classifier():
    return AIClassifier()

@pytest.mark.asyncio
async def test_classify_greeting(classifier):
    """Test classification of greeting message"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "scenario": "GREETING",
        "confidence": 0.95,
        "reasoning": "Клиент впервые обращается"
    })
    
    with patch.object(classifier.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
        result = await classifier.classify("Привет!")
        
        assert result["success"] is True
        assert result["scenario"] == "GREETING"
        assert result["confidence"] == 0.95

@pytest.mark.asyncio
async def test_classify_low_confidence(classifier):
    """Test that low confidence results in UNKNOWN"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "scenario": "REFERRAL",
        "confidence": 0.7,  # Below threshold
        "reasoning": "Might be referral"
    })
    
    with patch.object(classifier.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
        result = await classifier.classify("Something random")
        
        assert result["success"] is True
        assert result["scenario"] == "UNKNOWN"  # Downgraded due to low confidence

@pytest.mark.asyncio
async def test_classify_invalid_response(classifier):
    """Test handling of invalid response"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "{invalid json"
    
    with patch.object(classifier.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
        result = await classifier.classify("test")
        
        assert result["success"] is False
        assert result["scenario"] == "UNKNOWN"
        assert "error" in result

def test_validate_response(classifier):
    """Test response validation"""
    # Valid response
    valid = {
        "scenario": "GREETING",
        "confidence": 0.95,
        "reasoning": "test"
    }
    assert classifier._validate_response(valid) is True
    
    # Missing field
    invalid1 = {
        "scenario": "GREETING",
        "confidence": 0.95
    }
    assert classifier._validate_response(invalid1) is False
    
    # Invalid scenario
    invalid2 = {
        "scenario": "INVALID_SCENARIO",
        "confidence": 0.95,
        "reasoning": "test"
    }
    assert classifier._validate_response(invalid2) is False
    
    # Invalid confidence
    invalid3 = {
        "scenario": "GREETING",
        "confidence": 1.5,
        "reasoning": "test"
    }
    assert classifier._validate_response(invalid3) is False
