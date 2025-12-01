export type ScenarioType = "GREETING" | "REFERRAL" | "TECH_SUPPORT_BASIC" | "FAREWELL" | "REMINDER" | "ABSENCE_REQUEST" | "SCHEDULE_CHANGE" | "COMPLAINT" | "MISSING_TRAINER" | "MASS_OUTAGE" | "REVIEW_BONUS" | "CROSS_EXTENSION" | "UNKNOWN";

export type MessageType = "user" | "bot_auto" | "bot_escalated" | "operator";

export type PriorityLevel = "low" | "medium" | "high" | "critical";

export type EscalationReason = "low_confidence" | "repeated_failed" | "complaint" | "unknown_scenario" | "operator_marked" | "system_error";

export type FeedbackType = "correct" | "incorrect" | "needs_escalation";

export interface Message {
  id: string;
  client_id: string;
  content: string;
  message_type: MessageType;
  priority: PriorityLevel;
  escalation_reason?: EscalationReason | null;
  is_first_message: boolean;
  created_at: string;
}

export interface Classification {
  id: string;
  message_id: string;
  detected_scenario: ScenarioType;
  confidence: number;
  ai_model: string;
  created_at: string;
  reasoning?: string | null;
}

export interface OperatorFeedback {
  id: string;
  message_id: string;
  feedback_type: FeedbackType;
  suggested_scenario?: ScenarioType;
  comment?: string;
  operator_id: string;
  created_at: string;
}

export type DialogStatus = "open" | "closed" | "escalated";

export interface ChatSession {
  id: string;
  client_id: string;
  status: DialogStatus;
  last_activity_at: string;
  closed_at?: string;
  farewell_sent_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionWithMessages extends ChatSession {
  messages: Message[];
  classifications: Classification[];
  latest_classification?: Classification;
  has_escalation: boolean;
  last_message_at: string;
}

export interface MessageWithClassification extends Message {
  classification?: Classification;
}

export interface ClientSummary {
  client_id: string;
  last_message: string;
  last_message_at: string;
  message_count: number;
  has_pending: boolean;
  latest_scenario?: ScenarioType;
  latest_confidence?: number;
}
