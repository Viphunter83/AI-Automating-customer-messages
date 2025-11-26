import pytest
from unittest.mock import AsyncMock, patch
from app.services.ai_classifier import AIClassifier
from app.models.database import ScenarioType

@pytest.mark.asyncio
async def test_classify_greeting():
    """Test greeting classification"""
    classifier = AIClassifier()
    
    # Mock OpenAI response
    with patch.object(classifier, 'client') as mock_client:
        mock_response = {
            "scenario": "GREETING",
            "confidence": 0.95,
            "reasoning": "Клиент впервые обращается"
        }
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # TODO: Implement actual test when AIClassifier is ready
        pass

@pytest.mark.asyncio
async def test_classify_unknown():
    """Test unknown scenario handling"""
    classifier = AIClassifier()
    
    result = await classifier.classify("xxxyyyzzzaaa123random")
    assert result["scenario"] == "UNKNOWN" or result["confidence"] < 0.85

