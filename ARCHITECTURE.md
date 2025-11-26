# Архитектура проекта

## Общая структура

Проект разделен на два основных компонента:
- **Backend** (FastAPI) - обработка сообщений, классификация ИИ, управление данными
- **Frontend** (Next.js) - интерфейс операторов для мониторинга и фидбэка

## Backend структура

### `/backend/app/`

#### `config.py`
- Настройки приложения через Pydantic Settings
- Загрузка переменных окружения из `.env`
- Валидация конфигурации

#### `database.py`
- Подключение к PostgreSQL через SQLAlchemy async
- Создание engine и session factory
- Инициализация и закрытие соединений

#### `models/`
- **`schemas.py`** - Pydantic схемы для валидации запросов/ответов
- **`database.py`** - SQLAlchemy ORM модели

#### `routes/`
- **`health.py`** - Health check endpoints
- **`messages.py`** - Webhook для получения сообщений от чат-платформы
- **`feedback.py`** - Endpoint для фидбэка операторов

#### `services/`
- **`ai_classifier.py`** - Классификация сообщений через OpenAI (будет реализован)
- **`text_processor.py`** - Очистка и нормализация текста
- **`response_manager.py`** - Выбор и форматирование шаблонов ответов

#### `utils/`
- **`logger.py`** - Настройка логирования
- **`prompts.py`** - System prompts для ИИ

### `/backend/tests/`
- Unit тесты для сервисов
- Fixtures для тестовой БД

### `/backend/migrations/`
- Alembic миграции для управления схемой БД

## Frontend структура

### `/frontend/app/`
- **`layout.tsx`** - Root layout с Providers
- **`page.tsx`** - Главная страница
- **`dashboard/`** - Страницы дашборда операторов
- **`api/`** - Proxy endpoints к FastAPI

### `/frontend/components/`
- **`ChatHistory.tsx`** - Компонент истории диалога
- **`MessageFeedback.tsx`** - Форма фидбэка оператора
- **`ClientDashboard.tsx`** - Таблица клиентов/чатов
- **`ui/`** - shadcn/ui компоненты (будет добавлено)

### `/frontend/lib/`
- **`api.ts`** - API клиент (axios)
- **`types.ts`** - TypeScript интерфейсы
- **`utils.ts`** - Utility функции

### `/frontend/hooks/`
- React hooks для работы с данными (TanStack Query)

## База данных

### Таблицы:
- **`messages`** - Сообщения от клиентов
- **`classifications`** - Результаты классификации ИИ
- **`response_templates`** - Шаблоны ответов
- **`keywords`** - Ключевые слова для классификации
- **`operator_feedback`** - Фидбэк операторов
- **`operator_session_logs`** - Логи сессий операторов

## Поток данных

1. **Получение сообщения**: Webhook → `POST /api/messages/`
2. **Классификация**: Текст → AI Classifier → Scenario Type
3. **Выбор ответа**: Scenario → Response Template → Форматированный ответ
4. **Отправка ответа**: Ответ → Чат-платформа
5. **Фидбэк оператора**: `POST /api/feedback/` → Сохранение → Переобучение (будущее)

## Технологии

- **Backend**: FastAPI, SQLAlchemy, Pydantic, OpenAI
- **Frontend**: Next.js 14, TypeScript, TanStack Query, Tailwind CSS
- **Database**: PostgreSQL (Supabase)
- **Deployment**: Docker, Docker Compose

