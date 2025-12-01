/**
 * Mock data for demonstration purposes
 * These are sample messages and classifications to showcase the system functionality
 */

import { Message, Classification } from './types'

// Mock messages with various scenarios
export const mockMessages: Message[] = [
  {
    id: 'msg-001',
    client_id: 'client_123',
    content: 'Привет! Хочу узнать про реферальную программу',
    message_type: 'user',
    priority: 'low',
    escalation_reason: null,
    is_first_message: true,
    created_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
  },
  {
    id: 'msg-002',
    client_id: 'client_123',
    content: 'Здравствуйте! 👋 Рады видеть вас.\n\nЯ помощник первой линии поддержки. Чем я могу вам помочь?',
    message_type: 'bot_auto',
    priority: 'low',
    escalation_reason: null,
    is_first_message: false,
    created_at: new Date(Date.now() - 3590000).toISOString(),
  },
  {
    id: 'msg-003',
    client_id: 'client_123',
    content: 'Как работает реферальная программа? Сколько можно заработать?',
    message_type: 'user',
    priority: 'medium',
    escalation_reason: null,
    is_first_message: false,
    created_at: new Date(Date.now() - 3500000).toISOString(),
  },
  {
    id: 'msg-004',
    client_id: 'client_123',
    content: 'Реферальная программа позволяет вам приглашать друзей и получать бонусы за каждого приглашенного пользователя. За каждого активного реферала вы получаете 500 рублей на счет.',
    message_type: 'bot_auto',
    priority: 'medium',
    escalation_reason: null,
    is_first_message: false,
    created_at: new Date(Date.now() - 3490000).toISOString(),
  },
  {
    id: 'msg-005',
    client_id: 'client_456',
    content: 'У меня проблема с оплатой! Не могу пополнить счет уже 2 дня!',
    message_type: 'user',
    priority: 'high',
    escalation_reason: 'complaint',
    is_first_message: true,
    created_at: new Date(Date.now() - 1800000).toISOString(), // 30 min ago
  },
  {
    id: 'msg-006',
    client_id: 'client_456',
    content: 'Спасибо за обращение! Ваш запрос принят и передан оператору для обработки. Мы свяжемся с вами в ближайшее время для решения вашего вопроса.',
    message_type: 'bot_escalated',
    priority: 'high',
    escalation_reason: 'complaint',
    is_first_message: false,
    created_at: new Date(Date.now() - 1790000).toISOString(),
  },
  {
    id: 'msg-007',
    client_id: 'client_789',
    content: 'Как изменить расписание тренировок?',
    message_type: 'user',
    priority: 'low',
    escalation_reason: null,
    is_first_message: true,
    created_at: new Date(Date.now() - 900000).toISOString(), // 15 min ago
  },
  {
    id: 'msg-008',
    client_id: 'client_789',
    content: 'Вы можете изменить расписание тренировок через личный кабинет в разделе "Мои тренировки" или связавшись с вашим тренером.',
    message_type: 'bot_auto',
    priority: 'low',
    escalation_reason: null,
    is_first_message: false,
    created_at: new Date(Date.now() - 890000).toISOString(),
  },
]

// Mock classifications
export const mockClassifications: Classification[] = [
  {
    id: 'cls-001',
    message_id: 'msg-001',
    detected_scenario: 'GREETING',
    confidence: 0.92,
    ai_model: 'gpt-4o-mini',
    created_at: new Date(Date.now() - 3600000).toISOString(),
    reasoning: 'Клиент приветствует и обращается за помощью, что указывает на первое знакомство.',
  },
  {
    id: 'cls-002',
    message_id: 'msg-003',
    detected_scenario: 'REFERRAL',
    confidence: 0.88,
    ai_model: 'gpt-4o-mini',
    created_at: new Date(Date.now() - 3500000).toISOString(),
    reasoning: 'Клиент спрашивает о реферальной программе и возможности заработка.',
  },
  {
    id: 'cls-003',
    message_id: 'msg-005',
    detected_scenario: 'COMPLAINT',
    confidence: 0.95,
    ai_model: 'gpt-4o-mini',
    created_at: new Date(Date.now() - 1800000).toISOString(),
    reasoning: 'Клиент выражает недовольство проблемой с оплатой, использует восклицательные знаки, указывает на длительность проблемы.',
  },
  {
    id: 'cls-004',
    message_id: 'msg-007',
    detected_scenario: 'SCHEDULE_CHANGE',
    confidence: 0.85,
    ai_model: 'gpt-4o-mini',
    created_at: new Date(Date.now() - 900000).toISOString(),
    reasoning: 'Клиент спрашивает о возможности изменения расписания тренировок.',
  },
]

// Helper function to combine messages with classifications
export function getMockMessagesWithClassifications(clientId: string): Array<Message & { classification?: Classification }> {
  const clientMessages = mockMessages.filter(m => m.client_id === clientId)
  return clientMessages.map(msg => {
    const classification = mockClassifications.find(c => c.message_id === msg.id)
    return {
      ...msg,
      classification,
    }
  })
}

// Mock client IDs for demo
export const mockClientIds = ['client_123', 'client_456', 'client_789']

