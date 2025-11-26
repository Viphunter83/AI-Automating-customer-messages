from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ScenarioType(str, Enum):
    GREETING = "GREETING"
    REFERRAL = "REFERRAL"
    TECH_SUPPORT_BASIC = "TECH_SUPPORT_BASIC"
    UNKNOWN = "UNKNOWN"

class MessageTypeEnum(str, Enum):
    USER = "user"
    BOT_AUTO = "bot_auto"
    BOT_ESCALATED = "bot_escalated"
    OPERATOR = "operator"

# ========== MESSAGE SCHEMAS ==========

class MessageCreate(BaseModel):
    client_id: str = Field(..., min_length=1, description="Unique client ID from chat platform")
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class MessageResponse(BaseModel):
    id: str
    client_id: str
    content: str
    message_type: MessageTypeEnum
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== CLASSIFICATION SCHEMAS ==========

class ClassificationCreate(BaseModel):
    message_id: str
    detected_scenario: ScenarioType
    confidence: float = Field(..., ge=0.0, le=1.0)
    ai_model: str = "openai_4o_mini"
    reasoning: Optional[str] = None

class ClassificationResponse(BaseModel):
    id: str
    message_id: str
    detected_scenario: ScenarioType
    confidence: float
    ai_model: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== RESPONSE TEMPLATE SCHEMAS ==========

class ResponseTemplateCreate(BaseModel):
    scenario_name: ScenarioType
    template_text: str = Field(..., min_length=10)
    requires_params: dict = Field(default_factory=dict)

class ResponseTemplateUpdate(BaseModel):
    template_text: Optional[str] = None
    requires_params: Optional[dict] = None
    is_active: Optional[bool] = None

class ResponseTemplateResponse(BaseModel):
    id: str
    scenario_name: ScenarioType
    template_text: str
    requires_params: dict
    version: int
    is_active: bool
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ========== OPERATOR FEEDBACK SCHEMAS ==========

class FeedbackTypeEnum(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    NEEDS_ESCALATION = "needs_escalation"

class OperatorFeedbackCreate(BaseModel):
    message_id: str
    classification_id: str
    feedback_type: FeedbackTypeEnum
    suggested_scenario: Optional[ScenarioType] = None
    comment: Optional[str] = None
    operator_id: str

class OperatorFeedbackResponse(BaseModel):
    id: str
    message_id: str
    feedback_type: FeedbackTypeEnum
    suggested_scenario: Optional[ScenarioType]
    comment: Optional[str]
    operator_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== OPERATOR SESSION LOGS ==========

class OperatorSessionLogResponse(BaseModel):
    id: str
    client_id: str
    bot_interaction_history: list
    escalated_at: Optional[datetime]
    operator_id: Optional[str]
    resolution_notes: Optional[str]
    
    class Config:
        from_attributes = True

