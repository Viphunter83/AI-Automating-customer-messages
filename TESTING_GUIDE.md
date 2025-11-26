# 🧪 Руководство по тестированию системы

## ✅ Выполненные задачи

### 1. UI Компоненты
Все недостающие компоненты созданы в едином стиле:

- ✅ **Button** (`components/ui/button.tsx`)
  - 6 вариантов: default, destructive, outline, secondary, ghost, link
  - 4 размера: default, sm, lg, icon
  - Полная поддержка accessibility

- ✅ **Badge** (`components/ui/badge.tsx`)
  - 6 вариантов: default, secondary, destructive, outline, success, warning
  - Адаптивный дизайн

- ✅ **Input** (`components/ui/input.tsx`)
  - Полная поддержка всех HTML input атрибутов
  - Focus states и accessibility

- ✅ **Card** (`components/ui/card.tsx`)
- ✅ **Tabs** (`components/ui/tabs.tsx`)

### 2. Тестовые данные
Скрипт для создания тестовых данных: `backend/scripts/create_test_data.py`

### 3. TypeScript
Все ошибки исправлены ✅

## 🚀 Запуск системы

### Вариант 1: Полный запуск через Docker Compose

```bash
# 1. Запустить все сервисы
docker-compose up -d

# 2. Подождать запуска (10-15 секунд)
sleep 15

# 3. Создать тестовые данные
docker-compose exec backend python3 scripts/create_test_data.py

# 4. Проверить статус
docker-compose ps
```

### Вариант 2: Использование тестового скрипта

```bash
# Запустить автоматический тест
./scripts/test_system.sh
```

## 📊 Проверка работы

### 1. Проверка API

```bash
# Health check
curl http://localhost:8000/health

# Статистика сообщений
curl http://localhost:8000/api/admin/stats/messages

# Feedback summary
curl http://localhost:8000/api/admin/feedback/summary

# Список шаблонов
curl http://localhost:8000/api/admin/templates
```

### 2. Проверка Frontend

Откройте в браузере:
- **Dashboard**: http://localhost:3000/dashboard
- **Admin**: http://localhost:3000/admin
- **API Docs**: http://localhost:8000/docs

### 3. Тестирование отправки сообщения

```bash
curl -X POST http://localhost:8000/api/messages/ \
  -H "Content-Type: application/json" \
  -H "X-Webhook-URL: http://localhost:9000/webhook" \
  -d '{
    "client_id": "test_client_001",
    "content": "Привет! Как работает реферальная программа?"
  }'
```

## 🧪 Запуск тестов

```bash
# Backend тесты
cd backend
pytest tests/ -v

# Frontend type check
cd frontend
npm run type-check
```

## 📝 Тестовые данные

После запуска `create_test_data.py` в БД будут созданы:

- **3 клиента**: client_001, client_002, client_003
- **6 сообщений** с классификациями
- **3 фидбэка** от операторов
- **9 ключевых слов** для разных сценариев
- **4 шаблона ответов** (инициализируются автоматически)

## 🔍 Проверка БД

```bash
# Подключиться к PostgreSQL
docker-compose exec postgres psql -U support_user -d ai_support

# Проверить таблицы
\dt

# Посчитать записи
SELECT 'messages' as table_name, COUNT(*) FROM messages
UNION ALL
SELECT 'classifications', COUNT(*) FROM classifications
UNION ALL
SELECT 'operator_feedback', COUNT(*) FROM operator_feedback
UNION ALL
SELECT 'response_templates', COUNT(*) FROM response_templates
UNION ALL
SELECT 'keywords', COUNT(*) FROM keywords;
```

## ⚠️ Устранение проблем

### Проблема: "role support_user does not exist"
**Решение**: Убедитесь, что PostgreSQL контейнер запущен:
```bash
docker-compose up -d postgres
```

### Проблема: "relation does not exist"
**Решение**: Запустите миграции:
```bash
docker-compose exec backend alembic upgrade head
```

### Проблема: Backend не запускается
**Решение**: Проверьте логи:
```bash
docker-compose logs backend
```

### Проблема: Frontend ошибки TypeScript
**Решение**: Установите зависимости:
```bash
cd frontend
npm install
```

## 📈 Мониторинг

### Логи сервисов

```bash
# Все логи
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только frontend
docker-compose logs -f frontend
```

### Проверка здоровья

```bash
# API health
curl http://localhost:8000/health

# DB health
curl http://localhost:8000/health/db
```

## 🎯 Следующие шаги

1. ✅ UI компоненты созданы
2. ✅ TypeScript ошибки исправлены
3. ⏳ Запустить систему и создать тестовые данные
4. ⏳ Протестировать все endpoints
5. ⏳ Проверить работу админки и дашборда

