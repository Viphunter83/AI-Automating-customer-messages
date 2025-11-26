# 🚀 Полное руководство по деплою

**Дата:** 2025-11-26  
**План:** Railway (БД) + Vercel (Backend)

---

## 📋 План деплоя

1. ✅ **Railway** - База данных PostgreSQL
2. ✅ **Vercel** - FastAPI Backend (Serverless Functions)
3. ⚠️ **Frontend** - Можно задеплоить на Vercel или Netlify отдельно

---

## 🚂 Шаг 1: Настройка Railway для БД

### 1.1 Создание проекта Railway

1. Зайдите на [railway.app](https://railway.app)
2. Войдите через GitHub/GitLab/Email
3. **New Project** → **Deploy from GitHub repo** (опционально) или **Empty Project**

### 1.2 Добавление PostgreSQL

1. В проекте нажмите **+ New**
2. Выберите **Database** → **Add PostgreSQL**
3. Дождитесь создания инстанса (1-2 минуты)

### 1.3 Получение DATABASE_URL

1. Откройте созданную БД
2. Перейдите на вкладку **Variables**
3. Найдите `DATABASE_URL` или `POSTGRES_URL`
4. Скопируйте значение

**Пример:**
```
postgresql://postgres:password@containers-us-west-123.railway.app:5432/railway
```

**Для нашего проекта (asyncpg):**
```
postgresql+asyncpg://postgres:password@containers-us-west-123.railway.app:5432/railway
```

### 1.4 Применение миграций

**Вариант 1: Через Railway CLI**
```bash
npm i -g @railway/cli
railway login
railway link  # Подключитесь к проекту
railway run alembic upgrade head
```

**Вариант 2: Локально**
```bash
export DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway"
cd backend
alembic upgrade head
```

---

## 🚀 Шаг 2: Деплой на Vercel

### 2.1 Инициализация проекта Vercel

```bash
# Убедитесь, что вы в корне проекта
cd /Users/apple/AI\ Automating\ customer\ messages

# Инициализация проекта
vercel
```

Следуйте инструкциям:
- Выберите команду: `team_ckk1yHJodr9A9k87ScdWHwmQ` (Oleg's projects)
- Или создайте новый проект
- Подтвердите настройки

### 2.2 Настройка переменных окружения в Vercel

**Через Dashboard:**
1. Откройте проект в [Vercel Dashboard](https://vercel.com/dashboard)
2. Settings → Environment Variables
3. Добавьте переменные:

**Обязательные:**
```bash
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway
OPENAI_API_KEY=sk-your-api-key
SECRET_KEY=your-secret-key-minimum-32-characters-long
```

**Опциональные:**
```bash
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
OPENAI_MODEL=gpt-4o-mini
DEBUG=False
LOG_LEVEL=INFO
ALLOWED_ORIGINS=["https://your-frontend.vercel.app"]
```

**Через CLI:**
```bash
vercel env add DATABASE_URL production
vercel env add OPENAI_API_KEY production
vercel env add SECRET_KEY production
# ... и так далее
```

### 2.3 Деплой

```bash
# Preview deployment (для тестирования)
vercel

# Production deployment
vercel --prod
```

---

## ✅ Шаг 3: Проверка после деплоя

После успешного деплоя проверьте:

```bash
# Health check
curl https://your-project.vercel.app/health

# API docs
open https://your-project.vercel.app/docs

# Тест создания сообщения
curl -X POST https://your-project.vercel.app/api/messages/ \
  -H "Content-Type: application/json" \
  -d '{"client_id": "test", "content": "Привет"}'
```

---

## 🔧 Настройка Cron Jobs для Scheduler

Так как APScheduler не работает на serverless, используйте Vercel Cron Jobs.

Добавьте в `vercel.json`:

```json
{
  "crons": [
    {
      "path": "/api/reminders/process",
      "schedule": "*/5 * * * *"
    },
    {
      "path": "/api/dialogs/auto-close",
      "schedule": "*/2 * * * *"
    }
  ]
}
```

Создайте endpoints для cron jobs в `backend/app/routes/reminders.py` и `backend/app/routes/dialogs.py`.

---

## ⚠️ Важные замечания

### База данных
- ✅ Используйте Railway PostgreSQL (внешняя БД)
- ✅ Не используйте локальную БД на Vercel
- ✅ Примените миграции после создания БД

### WebSocket
- ⚠️ WebSocket endpoints (`/ws`) не работают на Vercel
- 💡 Используйте Vercel Realtime или внешний сервис

### Scheduler
- ⚠️ APScheduler не работает на serverless
- ✅ Используйте Vercel Cron Jobs

### Файловая система
- ⚠️ Read-only файловая система
- ✅ Используйте внешнее хранилище для файлов

---

## 📊 Архитектура после деплоя

```
┌─────────────┐
│   Vercel    │  ← FastAPI Backend (Serverless)
│  (Backend)  │
└──────┬──────┘
       │
       │ DATABASE_URL
       │
┌──────▼──────┐
│   Railway   │  ← PostgreSQL Database
│   (PostgreSQL)│
└─────────────┘
```

---

## 🎯 Следующие шаги

1. ✅ Создать БД на Railway
2. ✅ Применить миграции
3. ✅ Настроить переменные в Vercel
4. ✅ Задеплоить на Vercel
5. ⚠️ Настроить Cron Jobs (если нужно)
6. ⚠️ Настроить WebSocket альтернативу (если нужно)

---

**Готово к деплою!** 🚀

