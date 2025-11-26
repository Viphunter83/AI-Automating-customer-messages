# 🚀 Пошаговый деплой: Railway + Vercel

**Дата:** 2025-11-26

---

## 🎯 План

1. **Railway** → PostgreSQL база данных
2. **Vercel** → FastAPI Backend
3. **Frontend** → Можно задеплоить отдельно на Vercel или Netlify

---

## 🚂 ШАГ 1: Railway - База данных

### 1.1 Создание аккаунта и проекта

1. Откройте [railway.app](https://railway.app)
2. Войдите через GitHub (рекомендуется) или Email
3. Нажмите **New Project**
4. Выберите **Empty Project** или **Deploy from GitHub repo**

### 1.2 Добавление PostgreSQL

1. В проекте нажмите **+ New**
2. Выберите **Database** → **Add PostgreSQL**
3. Дождитесь создания (1-2 минуты)

### 1.3 Получение DATABASE_URL

1. Откройте созданную БД (PostgreSQL)
2. Перейдите на вкладку **Variables**
3. Найдите `DATABASE_URL` или `POSTGRES_URL`
4. Скопируйте значение

**Важно:** Измените формат для asyncpg:
- Было: `postgresql://postgres:password@host:5432/railway`
- Нужно: `postgresql+asyncpg://postgres:password@host:5432/railway`

### 1.4 Применение миграций

**Вариант A: Через Railway CLI**
```bash
npm i -g @railway/cli
railway login
railway link  # Выберите ваш проект
cd backend
railway run alembic upgrade head
```

**Вариант B: Локально**
```bash
export DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway"
cd backend
alembic upgrade head
```

---

## 🚀 ШАГ 2: Vercel - Backend

### 2.1 Инициализация проекта Vercel

```bash
# Убедитесь, что вы в корне проекта
cd /Users/apple/AI\ Automating\ customer\ messages

# Инициализация проекта
vercel
```

**Интерактивные вопросы:**
- **Set up and deploy?** → `Y`
- **Which scope?** → Выберите команду `team_ckk1yHJodr9A9k87ScdWHwmQ` (Oleg's projects)
- **Link to existing project?** → `N` (создать новый)
- **Project name?** → `ai-customer-support-backend` (или любое имя)
- **Directory?** → `.` (текущая директория)
- **Override settings?** → `N`

После этого создастся папка `.vercel` с конфигурацией.

### 2.2 Настройка переменных окружения

**Через Vercel Dashboard (рекомендуется):**

1. Откройте [vercel.com/dashboard](https://vercel.com/dashboard)
2. Найдите ваш проект
3. Settings → Environment Variables
4. Добавьте переменные:

**Обязательные:**
```
DATABASE_URL = postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway
OPENAI_API_KEY = sk-your-api-key-here
SECRET_KEY = your-secret-key-minimum-32-characters-long-change-this
```

**Опциональные:**
```
OPENAI_API_BASE = https://api.proxyapi.ru/openai/v1
OPENAI_MODEL = gpt-4o-mini
DEBUG = False
LOG_LEVEL = INFO
ALLOWED_ORIGINS = ["https://your-frontend.vercel.app","https://your-domain.com"]
```

**Важно:** Выберите окружения: Production, Preview, Development

### 2.3 Деплой

```bash
# Preview deployment (для тестирования)
vercel

# Production deployment
vercel --prod
```

После деплоя вы получите URL вида: `https://your-project.vercel.app`

---

## ✅ ШАГ 3: Проверка

После деплоя проверьте:

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

## 🌐 Про Netlify

**Netlify подходит, но Vercel лучше для FastAPI:**

### Почему Vercel лучше:
- ✅ Лучшая поддержка ASGI/FastAPI
- ✅ Больше времени выполнения (30 сек vs 10 сек)
- ✅ Больше документации для Python
- ✅ Лучшая производительность

### Когда использовать Netlify:
- Если нужны встроенные формы
- Если проект очень простой
- Если уже есть опыт с Netlify

**Рекомендация:** Используйте **Vercel для бэкенда**, Netlify можно использовать для frontend если нужно.

---

## ⚠️ Важные замечания

### База данных
- ✅ **ОБЯЗАТЕЛЬНО** используйте внешнюю БД (Railway)
- ❌ НЕ используйте локальную БД на Vercel
- ✅ Примените миграции после создания БД

### WebSocket
- ⚠️ WebSocket (`/ws`) не работает на Vercel
- 💡 Используйте Vercel Realtime или внешний сервис

### Scheduler
- ⚠️ APScheduler не работает на serverless
- ✅ Используйте Vercel Cron Jobs (см. ниже)

---

## 🔧 Настройка Cron Jobs (опционально)

Для периодических задач (напоминания, автозакрытие диалогов):

Добавьте в `vercel.json`:
```json
{
  "crons": [
    {
      "path": "/api/reminders/process",
      "schedule": "*/5 * * * *"
    }
  ]
}
```

И создайте соответствующие endpoints.

---

## 📊 Итоговая архитектура

```
┌─────────────┐
│   Vercel    │  ← FastAPI Backend (Serverless)
│  (Backend)  │     https://your-project.vercel.app
└──────┬──────┘
       │
       │ DATABASE_URL
       │
┌──────▼──────┐
│   Railway   │  ← PostgreSQL Database
│   (PostgreSQL)│   postgresql+asyncpg://...
└─────────────┘
```

---

## 🎯 Готово!

Следуйте шагам выше для деплоя. Если возникнут вопросы - обращайтесь!

**Следующий шаг:** Создайте БД на Railway и получите DATABASE_URL 🚂

