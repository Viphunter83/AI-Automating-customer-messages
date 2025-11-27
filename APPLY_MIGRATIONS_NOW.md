# 🗄️ Применить миграции к Railway PostgreSQL

**Дата:** 2025-11-27  
**Статус:** База данных пустая, нужно создать таблицы

---

## ✅ Да, база данных пустая!

После создания нового PostgreSQL сервиса в Railway база данных пустая - в ней нет таблиц. Нужно применить миграции Alembic.

---

## 🚀 Решение: Применить миграции

### Способ 1: Через Railway CLI (если авторизованы)

```bash
# 1. Авторизуйтесь (если еще не авторизованы)
railway login

# 2. Подключитесь к проекту
railway link

# 3. Выберите сервис PostgreSQL
railway service
# Выберите PostgreSQL (не приложение!)

# 4. Примените миграции
cd backend
railway run alembic upgrade head
```

---

### Способ 2: Локально с Railway DATABASE_URL (проще!)

#### Шаг 1: Получите DATABASE_URL из Railway

1. Railway Dashboard → PostgreSQL сервис → Variables
2. Найдите `DATABASE_URL` или `POSTGRES_URL`
3. Нажмите "show" чтобы увидеть пароль
4. Скопируйте полный URL

**Пример:**
```
postgresql://postgres:ВАШ_ПАРОЛЬ@trolley.proxy.rlwy.net:37852/railway
```

**ВАЖНО:** Для миграций используйте `postgresql://` (без `+asyncpg`), так как Alembic использует синхронный драйвер.

#### Шаг 2: Примените миграции локально

```bash
cd backend

# Установите DATABASE_URL (замените на ваш реальный URL!)
export DATABASE_URL="postgresql://postgres:ВАШ_ПАРОЛЬ@trolley.proxy.rlwy.net:37852/railway"

# Примените миграции
alembic upgrade head
```

---

## ✅ Что будет создано

После применения миграций будут созданы таблицы:

- ✅ `messages` - сообщения клиентов
- ✅ `classifications` - классификации AI
- ✅ `reminders` - напоминания
- ✅ `chat_sessions` - сессии чата
- ✅ `operator_feedback` - обратная связь операторов
- ✅ `response_templates` - шаблоны ответов
- ✅ Все индексы и ограничения

---

## 🎯 Проверка успешного применения

После успешного применения вы увидите:

```
INFO  [alembic.runtime.migration] Running upgrade -> 001_initial, Initial schema
INFO  [alembic.runtime.migration] Running upgrade 001_initial -> 002_add_scenarios, Add scenarios
INFO  [alembic.runtime.migration] Running upgrade 002_add_scenarios -> 003_add_reminders, Add reminders
INFO  [alembic.runtime.migration] Running upgrade 003_add_reminders -> 004_add_chat_sessions, Add chat sessions
INFO  [alembic.runtime.migration] Running upgrade 004_add_chat_sessions -> 005_add_message_priorities, Add message priorities
INFO  [alembic.runtime.migration] Running upgrade 005_add_message_priorities -> 006_add_performance_indexes, Add performance indexes
```

---

## ⚠️ ВАЖНО

1. **Для миграций используйте `postgresql://`** (без `+asyncpg`)
2. **Для приложения используйте `postgresql+asyncpg://`** (с `+asyncpg`)
3. **Используйте реальный URL из Railway**, а не `localhost`

---

**После применения миграций приложение сможет работать с базой данных!** 🚀

