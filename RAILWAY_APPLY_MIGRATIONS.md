# 🗄️ Применение миграций к Railway PostgreSQL

**Дата:** 2025-11-27  
**Проблема:** База данных пустая, нужно создать таблицы

---

## ✅ Да, база данных пустая!

После создания нового PostgreSQL сервиса в Railway база данных пустая - в ней нет таблиц. Нужно применить миграции Alembic.

---

## 🚀 Решение: Применить миграции

У вас есть 6 миграций:
1. `001_initial_schema.py` - основная схема
2. `002_add_scenarios.py` - сценарии
3. `003_add_reminders.py` - напоминания
4. `004_add_chat_sessions.py` - сессии чата
5. `005_add_message_priorities.py` - приоритеты сообщений
6. `006_add_performance_indexes.py` - индексы производительности

---

## 📋 Способ 1: Через Railway CLI (рекомендуется)

### Шаг 1: Подключитесь к проекту

```bash
cd "/Users/apple/AI Automating customer messages"
railway link
```

Выберите проект `AI-Automating-customer-messages`

### Шаг 2: Выберите сервис PostgreSQL

```bash
railway service
```

Выберите сервис **PostgreSQL** (не приложение!)

### Шаг 3: Примените миграции

```bash
cd backend
railway run alembic upgrade head
```

Это применит все миграции к базе данных Railway.

---

## 📋 Способ 2: Локально с Railway DATABASE_URL

### Шаг 1: Получите DATABASE_URL из Railway

1. Railway Dashboard → PostgreSQL сервис → Variables
2. Скопируйте `DATABASE_URL` (без `+asyncpg` для миграций!)
3. Пример: `postgresql://postgres:ПАРОЛЬ@trolley.proxy.rlwy.net:37852/railway`

### Шаг 2: Примените миграции локально

```bash
cd "/Users/apple/AI Automating customer messages/backend"
export DATABASE_URL="postgresql://postgres:ПАРОЛЬ@trolley.proxy.rlwy.net:37852/railway"
alembic upgrade head
```

**ВАЖНО:** Для миграций используйте `postgresql://` (без `+asyncpg`), так как Alembic использует синхронный драйвер `psycopg2`.

---

## ✅ Проверка после применения миграций

После успешного применения миграций вы увидите:

```
INFO  [alembic.runtime.migration] Running upgrade -> 001_initial, Initial schema
INFO  [alembic.runtime.migration] Running upgrade 001_initial -> 002_add_scenarios, Add scenarios
INFO  [alembic.runtime.migration] Running upgrade 002_add_scenarios -> 003_add_reminders, Add reminders
INFO  [alembic.runtime.migration] Running upgrade 003_add_reminders -> 004_add_chat_sessions, Add chat sessions
INFO  [alembic.runtime.migration] Running upgrade 004_add_chat_sessions -> 005_add_message_priorities, Add message priorities
INFO  [alembic.runtime.migration] Running upgrade 005_add_message_priorities -> 006_add_performance_indexes, Add performance indexes
```

---

## 🎯 Что будет создано

После применения миграций в базе данных будут созданы таблицы:

- `messages` - сообщения клиентов
- `classifications` - классификации AI
- `reminders` - напоминания
- `chat_sessions` - сессии чата
- `operator_feedback` - обратная связь операторов
- `response_templates` - шаблоны ответов
- И все необходимые индексы и ограничения

---

## ⚠️ ВАЖНО

1. **Применяйте миграции к PostgreSQL сервису**, а не к приложению
2. **Для миграций используйте `postgresql://`** (без `+asyncpg`)
3. **Для приложения используйте `postgresql+asyncpg://`** (с `+asyncpg`)

---

**После применения миграций приложение сможет работать с базой данных!** 🚀

