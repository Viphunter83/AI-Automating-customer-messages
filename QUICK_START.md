# ⚡ Быстрый старт: Railway + Vercel

**Дата:** 2025-11-26

---

## 🚂 ШАГ 1: Railway - База данных (5 минут)

### 1. Создайте БД на Railway

1. Откройте [railway.app](https://railway.app)
2. Войдите через GitHub или Email
3. **New Project** → **Empty Project**
4. **+ New** → **Database** → **Add PostgreSQL**
5. Дождитесь создания (1-2 минуты)

### 2. Получите DATABASE_URL

1. Откройте созданную PostgreSQL БД
2. Перейдите на **Variables**
3. Скопируйте `DATABASE_URL` или `POSTGRES_URL`

**Важно:** Измените формат для asyncpg:
```
Было:  postgresql://postgres:password@host:5432/railway
Нужно: postgresql+asyncpg://postgres:password@host:5432/railway
```

### 3. Примените миграции

**Через Railway CLI:**
```bash
npm i -g @railway/cli
railway login
railway link  # Выберите ваш проект
cd backend
railway run alembic upgrade head
```

**Или локально:**
```bash
export DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway"
cd backend
alembic upgrade head
```

---

## 🚀 ШАГ 2: Vercel - Backend (5 минут)

### 1. Инициализация проекта

```bash
cd /Users/apple/AI\ Automating\ customer\ messages
vercel
```

**Ответьте на вопросы:**
- Set up and deploy? → `Y`
- Which scope? → Выберите команду `team_ckk1yHJodr9A9k87ScdWHwmQ`
- Link to existing project? → `N`
- Project name? → `ai-customer-support-backend`
- Directory? → `.`
- Override settings? → `N`

### 2. Настройка переменных окружения

**Через Dashboard (рекомендуется):**

1. Откройте [vercel.com/dashboard](https://vercel.com/dashboard)
2. Найдите ваш проект → **Settings** → **Environment Variables**
3. Добавьте переменные:

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
```

**Важно:** Выберите окружения: ✅ Production, ✅ Preview, ✅ Development

### 3. Деплой

```bash
# Preview (для тестирования)
vercel

# Production
vercel --prod
```

После деплоя вы получите URL: `https://your-project.vercel.app`

---

## ✅ ШАГ 3: Проверка

```bash
# Health check
curl https://your-project.vercel.app/health

# API docs
open https://your-project.vercel.app/docs

# Тест API
curl -X POST https://your-project.vercel.app/api/messages/ \
  -H "Content-Type: application/json" \
  -d '{"client_id": "test", "content": "Привет"}'
```

---

## 🌐 Про Netlify

**Netlify подходит, но Vercel лучше для FastAPI:**

### Почему Vercel:
- ✅ Лучшая поддержка ASGI/FastAPI
- ✅ Больше времени выполнения (30 сек vs 10 сек)
- ✅ Больше документации для Python
- ✅ Лучшая производительность

### Когда Netlify:
- Если нужны встроенные формы
- Если проект очень простой
- Если уже есть опыт с Netlify

**Рекомендация:** Используйте **Vercel для бэкенда**, Netlify можно для frontend.

---

## ⚠️ Важно

1. ✅ **ОБЯЗАТЕЛЬНО** используйте внешнюю БД (Railway)
2. ✅ Примените миграции после создания БД
3. ⚠️ WebSocket (`/ws`) не работает на Vercel
4. ⚠️ APScheduler не работает на serverless (используйте Cron Jobs)

---

## 📚 Дополнительная документация

- `DEPLOYMENT_COMPLETE_GUIDE.md` - Полное руководство
- `STEP_BY_STEP_DEPLOY.md` - Пошаговая инструкция
- `RAILWAY_SETUP.md` - Детали Railway
- `VERCEL_SETUP_GUIDE.md` - Детали Vercel

---

**Готово! Начните с Railway, затем Vercel** 🚀

