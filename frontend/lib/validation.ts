import { z } from 'zod';

// Custom datetime validator that accepts ISO 8601 with or without timezone
const datetimeString = z.string().refine(
  (val) => {
    // Accept ISO 8601 format with or without timezone (Z or +HH:MM)
    // Examples: "2025-12-01T06:51:37.755262" or "2025-12-01T06:51:37.755262Z"
    const iso8601Regex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$/;
    return iso8601Regex.test(val) && !isNaN(Date.parse(val));
  },
  { message: "Invalid datetime format" }
);

// Message validation schema
export const MessageSchema = z.object({
  id: z.string().uuid(),
  client_id: z.string().min(1),
  content: z.string().min(1),
  message_type: z.enum(['user', 'bot_auto', 'bot_escalated', 'operator']),
  priority: z.enum(['low', 'medium', 'high', 'critical']),
  escalation_reason: z.enum([
    'low_confidence',
    'repeated_failed',
    'complaint',
    'unknown_scenario',
    'operator_marked',
    'system_error'
  ]).nullable().optional(),
  is_first_message: z.boolean(),
  created_at: datetimeString,
});

// Classification validation schema
export const ClassificationSchema = z.object({
  id: z.string().uuid(),
  message_id: z.string().uuid(),
  detected_scenario: z.enum([
    'GREETING',
    'REFERRAL',
    'TECH_SUPPORT_BASIC',
    'FAREWELL',
    'REMINDER',
    'ABSENCE_REQUEST',
    'SCHEDULE_CHANGE',
    'COMPLAINT',
    'MISSING_TRAINER',
    'MASS_OUTAGE',
    'REVIEW_BONUS',
    'CROSS_EXTENSION',
    'UNKNOWN'
  ]),
  confidence: z.number().min(0).max(1),
  ai_model: z.string(),
  created_at: datetimeString,
  reasoning: z.string().nullable().optional(),
});

// API Response schemas
export const MessageResponseSchema = z.array(MessageSchema);

export const ClassificationResponseSchema = z.array(ClassificationSchema);

export const ChatSessionSchema = z.object({
  id: z.string().uuid(),
  client_id: z.string().min(1),
  status: z.enum(['open', 'closed', 'escalated']),
  last_activity_at: datetimeString,
  closed_at: datetimeString.nullable().optional(),
  farewell_sent_at: datetimeString.nullable().optional(),
  created_at: datetimeString,
  updated_at: datetimeString,
});

export const CreateMessageResponseSchema = z.object({
  status: z.enum(['success', 'escalated', 'fallback', 'duplicate', 'error']),
  original_message_id: z.string().uuid(),
  is_first_message: z.boolean(),
  priority: z.enum(['low', 'medium', 'high', 'critical']),
  escalation_reason: z.string().nullable().optional(),
  classification: z.object({
    id: z.string().uuid(),
    scenario: z.string(),
    confidence: z.number(),
    reasoning: z.string().nullable().optional(),
  }).nullable().optional(),
  response: z.object({
    message_id: z.string().uuid().nullable(),
    text: z.string(),
    type: z.string(),
  }),
  webhook: z.object({
    success: z.boolean(),
    error: z.string().nullable().optional(),
  }).optional(),
});

// Error response schema
export const ErrorResponseSchema = z.object({
  detail: z.string(),
  error: z.string().optional(),
});

// Type guards
export function isValidMessage(data: unknown): data is z.infer<typeof MessageSchema> {
  try {
    MessageSchema.parse(data);
    return true;
  } catch {
    return false;
  }
}

export function isValidClassification(data: unknown): data is z.infer<typeof ClassificationSchema> {
  try {
    ClassificationSchema.parse(data);
    return true;
  } catch {
    return false;
  }
}

// Safe parse helpers
export function safeParseMessages(data: unknown) {
  return MessageResponseSchema.safeParse(data);
}

export function safeParseClassifications(data: unknown) {
  return ClassificationResponseSchema.safeParse(data);
}

export function safeParseCreateMessageResponse(data: unknown) {
  return CreateMessageResponseSchema.safeParse(data);
}

