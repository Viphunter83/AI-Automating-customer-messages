from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, Integer, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from datetime import datetime
import uuid
from enum import Enum

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

class MessageType(str, Enum):
    USER = "user"
    BOT_AUTO = "bot_auto"
    BOT_ESCALATED = "bot_escalated"
    OPERATOR = "operator"

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.USER, nullable=False)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    classifications = relationship("Classification", back_populates="message", cascade="all, delete-orphan")
    feedbacks = relationship("OperatorFeedback", back_populates="message", cascade="all, delete-orphan")

class Classification(Base):
    __tablename__ = "classifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, index=True)
    detected_scenario = Column(SQLEnum(ScenarioType), nullable=False)
    confidence = Column(Float, nullable=False)  # 0-1
    ai_model = Column(String(100), default="openai_4o_mini")
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    message = relationship("Message", back_populates="classifications")

class ResponseTemplate(Base):
    __tablename__ = "response_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_name = Column(SQLEnum(ScenarioType), unique=True, nullable=False)
    template_text = Column(Text, nullable=False)
    requires_params = Column(JSON, default={})
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_name = Column(SQLEnum(ScenarioType), nullable=False, index=True)
    keyword = Column(String(255), nullable=False)
    priority = Column(Integer, default=5)  # 1-10
    created_at = Column(DateTime, default=datetime.utcnow)

class OperatorFeedback(Base):
    __tablename__ = "operator_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, index=True)
    classification_id = Column(UUID(as_uuid=True), ForeignKey("classifications.id"), nullable=True)
    operator_id = Column(String(255), nullable=False)
    feedback_type = Column(String(50), nullable=False)  # 'correct', 'incorrect', 'needs_escalation'
    suggested_scenario = Column(SQLEnum(ScenarioType), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="feedbacks")

class OperatorSessionLog(Base):
    __tablename__ = "operator_session_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String(255), nullable=False, index=True)
    bot_interaction_history = Column(JSON, default=[])
    escalated_at = Column(DateTime, nullable=True)
    operator_id = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)

class ReminderType(str, Enum):
    REMINDER_15MIN = "reminder_15min"
    REMINDER_30MIN = "reminder_30min"
    REMINDER_1DAY = "reminder_1day"

class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String(255), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, index=True)
    reminder_type = Column(SQLEnum(ReminderType), nullable=False)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    is_cancelled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    message = relationship("Message", foreign_keys=[message_id])

