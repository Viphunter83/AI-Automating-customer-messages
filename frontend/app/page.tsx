'use client'

import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🤖 Система поддержки клиентов на базе ИИ
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Автоматическая классификация и обработка сообщений клиентов
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/demo">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
                🎬 Демонстрация
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline">
                📊 Панель оператора
              </Button>
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <Card className="p-6">
            <h2 className="text-2xl font-semibold mb-3">✨ Основные возможности</h2>
            <ul className="space-y-2 text-gray-700">
              <li>✅ Автоматическая классификация сообщений с помощью ИИ</li>
              <li>✅ Генерация ответов на основе сценариев</li>
              <li>✅ Эскалация сложных запросов операторам</li>
              <li>✅ Отслеживание приоритетов и статусов диалогов</li>
              <li>✅ Аналитика и отчетность</li>
              <li>✅ Обратная связь от операторов для улучшения ИИ</li>
            </ul>
          </Card>

          <Card className="p-6">
            <h2 className="text-2xl font-semibold mb-3">🚀 Быстрый старт</h2>
            <ol className="space-y-3 text-gray-700">
              <li>
                <strong>1. Демонстрация:</strong> Перейдите в раздел "Демо" и отправьте тестовые сообщения
              </li>
              <li>
                <strong>2. Панель оператора:</strong> Откройте панель оператора для просмотра диалогов
              </li>
              <li>
                <strong>3. Поиск:</strong> Используйте поиск для нахождения конкретных сообщений
              </li>
              <li>
                <strong>4. Аналитика:</strong> Просматривайте статистику и отчеты
              </li>
            </ol>
          </Card>
        </div>

        {/* Instructions */}
        <Card className="p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">📖 Инструкция для операторов</h2>
          
          <div className="space-y-4 text-gray-700">
            <div>
              <h3 className="font-semibold mb-2">1. Просмотр диалогов</h3>
              <p className="text-sm">
                В разделе "Панель инструментов" введите Client ID клиента для просмотра истории сообщений.
                Система автоматически отображает все сообщения с их классификациями.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-2">2. Обратная связь</h3>
              <p className="text-sm">
                Выберите сообщение из списка справа, чтобы просмотреть детали классификации.
                Вы можете оставить обратную связь, если ИИ неправильно классифицировал сообщение.
                Это поможет улучшить точность системы.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-2">3. Управление диалогами</h3>
              <p className="text-sm">
                Вы можете закрывать и переоткрывать диалоги. Закрытые диалоги автоматически получают
                прощальное сообщение через определенное время.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-2">4. Приоритеты</h3>
              <p className="text-sm">
                Сообщения автоматически получают приоритеты (low, medium, high, critical) на основе
                различных факторов: уверенности ИИ, типа сценария, повторяющихся запросов и т.д.
              </p>
            </div>
          </div>
        </Card>

        {/* API Integration */}
        <Card className="p-6 bg-blue-50 border-blue-200">
          <h2 className="text-2xl font-semibold mb-4">🔌 Интеграция с CRM</h2>
          <p className="text-gray-700 mb-4">
            Система готова к интеграции с вашей CRM системой. API принимает сообщения через POST запросы.
          </p>
          <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
            <div className="mb-2">POST /api/messages/</div>
            <div className="text-gray-400 mb-2">Headers:</div>
            <div className="ml-4 mb-2">Content-Type: application/json</div>
            <div className="ml-4 mb-4">X-Webhook-URL: (опционально) URL для отправки ответа</div>
            <div className="text-gray-400 mb-2">Body:</div>
            <div className="ml-4">{`{`}</div>
            <div className="ml-8">"client_id": "client_123",</div>
            <div className="ml-8">"content": "Текст сообщения клиента"</div>
            <div className="ml-4">{`}`}</div>
          </div>
          <Link href="/integration-guide" className="text-blue-600 hover:underline mt-4 inline-block">
            📚 Подробная документация по интеграции →
          </Link>
        </Card>
      </div>
    </div>
  )
}
