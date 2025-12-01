import html
import re
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ScenarioType(str, Enum):
    GREETING = "GREETING"
    REFERRAL = "REFERRAL"
    TECH_SUPPORT_BASIC = "TECH_SUPPORT_BASIC"
    FAREWELL = "FAREWELL"
    REMINDER = "REMINDER"
    ABSENCE_REQUEST = "ABSENCE_REQUEST"
    SCHEDULE_CHANGE = "SCHEDULE_CHANGE"
    COMPLAINT = "COMPLAINT"
    MISSING_TRAINER = "MISSING_TRAINER"
    MASS_OUTAGE = "MASS_OUTAGE"
    REVIEW_BONUS = "REVIEW_BONUS"
    CROSS_EXTENSION = "CROSS_EXTENSION"
    UNKNOWN = "UNKNOWN"
    ESCALATED = "ESCALATED"  # Special scenario for escalation notifications


class MessageTypeEnum(str, Enum):
    USER = "user"
    BOT_AUTO = "bot_auto"
    BOT_ESCALATED = "bot_escalated"
    OPERATOR = "operator"


# ========== MESSAGE SCHEMAS ==========


class MessageCreate(BaseModel):
    client_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique client ID from chat platform",
        pattern=r"^[a-zA-Z0-9_\-\.]+$",  # Only alphanumeric, underscore, dash, dot
    )
    content: str = Field(
        ..., min_length=1, max_length=5000, description="Message content"
    )
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, v: str) -> str:
        """Validate and sanitize client_id"""
        if not v or not v.strip():
            raise ValueError("client_id cannot be empty")

        # Remove any whitespace
        v = v.strip()

        # Check for suspicious patterns
        if re.search(r'[<>"\']', v):
            raise ValueError("client_id contains invalid characters")

        # Check length
        if len(v) > 255:
            raise ValueError("client_id exceeds maximum length of 255 characters")

        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate and sanitize message content"""
        if not v or not v.strip():
            raise ValueError("content cannot be empty")

        # Check for suspicious SQL patterns (basic check, main validation in middleware)
        dangerous_patterns = [
            r"(?i)(union\s+(all\s+)?select)",
            r"(?i)(;\s*(drop|delete|insert|update|exec))",
            r"(?i)(--\s*$)",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v):
                raise ValueError("content contains potentially dangerous patterns")

        # Escape HTML to prevent XSS (content will be stored as-is, but displayed safely)
        # Note: We don't fully escape here as content might contain legitimate formatting
        # The frontend should handle XSS prevention

        # Check for extremely long content (prevent DoS)
        if len(v) > 5000:
            raise ValueError("content exceeds maximum length of 5000 characters")

        return v.strip()

    @model_validator(mode="after")
    def validate_model(self):
        """Additional model-level validation"""
        # Ensure content is not just whitespace after validation
        if not self.content or not self.content.strip():
            raise ValueError("content cannot be empty or only whitespace")

        return self


class PriorityLevelEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationReasonEnum(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    REPEATED_FAILED = "repeated_failed"
    COMPLAINT = "complaint"
    UNKNOWN_SCENARIO = "unknown_scenario"
    OPERATOR_MARKED = "operator_marked"
    SYSTEM_ERROR = "system_error"


class MessageResponse(BaseModel):
    id: str
    client_id: str
    content: str
    message_type: MessageTypeEnum
    priority: PriorityLevelEnum = PriorityLevelEnum.LOW
    escalation_reason: Optional[EscalationReasonEnum] = None
    is_first_message: bool = False
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
    reasoning: Optional[str] = None

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


# ========== CHAT SESSION SCHEMAS ==========


class DialogStatusEnum(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    ESCALATED = "escalated"


class ChatSessionResponse(BaseModel):
    id: str
    client_id: str
    status: DialogStatusEnum
    last_activity_at: datetime
    closed_at: Optional[datetime] = None
    farewell_sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None
    last_message_preview: Optional[str] = None
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatSessionUpdate(BaseModel):
    status: Optional[DialogStatusEnum] = None
