'use client'

import { Card } from '@/components/ui/card'

export default function IntegrationGuidePage() {
  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">📚 Руководство по интеграции</h1>

      <Card className="p-6 mb-6">
        <h2 className="text-2xl font-semibold mb-4">🔌 API Endpoint</h2>
        <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm mb-4">
          <div>POST {process.env.NEXT_PUBLIC_API_URL || 'https://your-api-url.com'}/api/messages/</div>
        </div>
        
        <h3 className="font-semibold mb-2 mt-4">Заголовки (Headers):</h3>
        <ul className="list-disc list-inside space-y-1 text-gray-700 mb-4">
          <li><code className="bg-gray-100 px-1 rounded">Content-Type: application/json</code> (обязательно)</li>
          <li><code className="bg-gray-100 px-1 rounded">X-Webhook-URL: https://your-crm.com/webhook</code> (опционально) - URL для отправки ответа обратно</li>
          <li><code className="bg-gray-100 px-1 rounded">X-Idempotency-Key: unique-key-123</code> (опционально) - ключ для предотвращения дубликатов</li>
        </ul>

        <h3 className="font-semibold mb-2">Тело запроса (Body):</h3>
        <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm">
          <div>{`{`}</div>
          <div className="ml-4">"client_id": "client_123", <span className="text-gray-500">// Уникальный ID клиента</span></div>
          <div className="ml-4">"content": "Текст сообщения от клиента", <span className="text-gray-500">// Текст сообщения</span></div>
          <div className="ml-4">"timestamp": "2025-11-27T12:00:00Z" <span className="text-gray-500">// Опционально, по умолчанию текущее время</span></div>
          <div>{`}`}</div>
        </div>
      </Card>

      <Card className="p-6 mb-6">
        <h2 className="text-2xl font-semibold mb-4">📥 Ответ API</h2>
        <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm">
          <div>{`{`}</div>
          <div className="ml-4">"status": "success",</div>
          <div className="ml-4">"original_message_id": "uuid",</div>
          <div className="ml-4">"is_first_message": true,</div>
          <div className="ml-4">"priority": "low",</div>
          <div className="ml-4">"classification": {`{`}</div>
          <div className="ml-8">"scenario": "GREETING",</div>
          <div className="ml-8">"confidence": 0.92,</div>
          <div className="ml-8">"reasoning": "..."</div>
          <div className="ml-4">{`}`},</div>
          <div className="ml-4">"response": {`{`}</div>
          <div className="ml-8">"message_id": "uuid",</div>
          <div className="ml-8">"text": "Автоматический ответ...",</div>
          <div className="ml-8">"type": "bot_auto"</div>
          <div className="ml-4">{`}`},</div>
          <div className="ml-4">"webhook": {`{`}</div>
          <div className="ml-8">"success": true</div>
          <div className="ml-4">{`}`}</div>
          <div>{`}`}</div>
        </div>
      </Card>

      <Card className="p-6 mb-6">
        <h2 className="text-2xl font-semibold mb-4">🔄 Webhook для ответов</h2>
        <p className="text-gray-700 mb-4">
          Если вы указали заголовок <code className="bg-gray-100 px-1 rounded">X-Webhook-URL</code>,
          система автоматически отправит ответ обратно в вашу CRM систему.
        </p>
        <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm">
          <div>POST {`{your-webhook-url}`}</div>
          <div className="mt-2">{`{`}</div>
          <div className="ml-4">"client_id": "client_123",</div>
          <div className="ml-4">"response_text": "Автоматический ответ...",</div>
          <div className="ml-4">"message_id": "uuid",</div>
          <div className="ml-4">"classification": {`{`}</div>
          <div className="ml-8">"scenario": "GREETING",</div>
          <div className="ml-8">"confidence": 0.92</div>
          <div className="ml-4">{`}`}</div>
          <div>{`}`}</div>
        </div>
      </Card>

      <Card className="p-6 mb-6">
        <h2 className="text-2xl font-semibold mb-4">📊 Примеры сценариев</h2>
        <div className="space-y-2 text-gray-700">
          <div><strong>GREETING</strong> - Приветствие и первое обращение</div>
          <div><strong>REFERRAL</strong> - Вопросы о реферальной программе</div>
          <div><strong>TECH_SUPPORT_BASIC</strong> - Базовые технические вопросы</div>
          <div><strong>FAREWELL</strong> - Прощание</div>
          <div><strong>COMPLAINT</strong> - Жалобы (автоматически эскалируются)</div>
          <div><strong>SCHEDULE_CHANGE</strong> - Изменение расписания</div>
          <div><strong>UNKNOWN</strong> - Неизвестный сценарий (требует эскалации)</div>
        </div>
      </Card>

      <Card className="p-6 bg-yellow-50 border-yellow-200">
        <h2 className="text-2xl font-semibold mb-4">⚠️ Важные замечания</h2>
        <ul className="space-y-2 text-gray-700">
          <li>• Rate limiting: максимум 10 сообщений в минуту на одного клиента</li>
          <li>• Сообщения с низкой уверенностью ИИ автоматически эскалируются</li>
          <li>• Жалобы и повторяющиеся запросы получают высокий приоритет</li>
          <li>• Используйте X-Idempotency-Key для предотвращения дубликатов</li>
        </ul>
      </Card>
    </div>
  )
}

