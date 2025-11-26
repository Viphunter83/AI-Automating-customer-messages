import json
import logging
from typing import Dict, Optional
from openai import AsyncOpenAI
from app.config import get_settings
from app.utils.prompts import CLASSIFICATION_SYSTEM_PROMPT, CLASSIFICATION_USER_TEMPLATE
from app.models.database import ScenarioType
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class AIClassifier:
    """Classify client messages using OpenAI API"""
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
        )
        self.model = settings.openai_model
        self.confidence_threshold = settings.ai_confidence_threshold
        self.timeout = settings.ai_classification_timeout
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def classify(
        self,
        message: str,
        client_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Classify a client message into a scenario
        
        Args:
            message: The message text to classify
            client_id: Optional client ID for logging
        
        Returns:
            {
                "scenario": "GREETING|REFERRAL|...|UNKNOWN",
                "confidence": 0.95,
                "reasoning": "...",
                "success": True|False,
                "error": None|"error message"
            }
        """
        try:
            logger.info(f"Classifying message for client {client_id}: {message[:50]}...")
            
            # Build user message
            user_message = CLASSIFICATION_USER_TEMPLATE.format(message=message)
            
            # Call OpenAI API with JSON mode
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,  # Low temperature for consistent classification
                response_format={"type": "json_object"},
                timeout=self.timeout,
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            result = json.loads(response_text)
            
            # Validate response structure
            if not self._validate_response(result):
                logger.warning(f"Invalid response structure: {result}")
                return self._error_response("Invalid response format from AI")
            
            # Extract values
            scenario = result.get("scenario", "UNKNOWN")
            confidence = float(result.get("confidence", 0))
            reasoning = result.get("reasoning", "")
            
            # Apply confidence threshold
            if confidence < self.confidence_threshold:
                logger.debug(
                    f"Confidence {confidence} below threshold {self.confidence_threshold}, "
                    f"downgrading to UNKNOWN"
                )
                scenario = "UNKNOWN"
            
            logger.info(
                f"Classification result: scenario={scenario}, "
                f"confidence={confidence}, client={client_id}"
            )
            
            return {
                "scenario": scenario,
                "confidence": confidence,
                "reasoning": reasoning,
                "success": True,
                "error": None,
                "model": self.model,
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI: {e}")
            return self._error_response(f"JSON parse error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Classification error: {type(e).__name__}: {str(e)}")
            return self._error_response(f"Classification failed: {str(e)}")
    
    def _validate_response(self, response: Dict) -> bool:
        """Validate response has required fields"""
        required_fields = ["scenario", "confidence", "reasoning"]
        
        if not all(field in response for field in required_fields):
            return False
        
        # Validate scenario is valid
        valid_scenarios = [s.value for s in ScenarioType]
        if response["scenario"] not in valid_scenarios and response["scenario"] != "UNKNOWN":
            return False
        
        # Validate confidence is 0-1
        try:
            conf = float(response["confidence"])
            if not (0 <= conf <= 1):
                return False
        except (ValueError, TypeError):
            return False
        
        return True
    
    def _error_response(self, error_message: str) -> Dict[str, any]:
        """Return error response"""
        return {
            "scenario": "UNKNOWN",
            "confidence": 0,
            "reasoning": error_message,
            "success": False,
            "error": error_message,
            "model": self.model,
        }
