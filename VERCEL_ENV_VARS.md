# 🔐 Переменные окружения для Vercel

**Дата:** 2025-11-26

---

## 📋 Необходимые переменные окружения

Скопируйте эти переменные в Vercel Dashboard → Settings → Environment Variables

### 🔴 Обязательные переменные

```bash
# База данных (ОБЯЗАТЕЛЬНО использовать внешнюю БД!)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database

# OpenAI API
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
OPENAI_MODEL=gpt-4o-mini

# Безопасность
SECRET_KEY=your-secret-key-minimum-32-characters-long
```

### 🟡 Опциональные переменные

```bash
# Приложение
APP_NAME=AI Customer Support
APP_VERSION=1.0.0
DEBUG=False
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=["https://your-frontend.vercel.app","https://your-domain.com"]

# AI настройки
AI_CLASSIFICATION_TIMEOUT=30
AI_CONFIDENCE_THRESHOLD=0.85

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_MESSAGE_PER_MINUTE=10

# Задержки отправки
RESPONSE_DELAY_SECONDS=3.0
FAREWELL_DELAY_SECONDS=10.0
DELAYS_ENABLED=True

# Supabase (если используется)
SUPABASE_URL=
SUPABASE_ANON_KEY=
```

---

## ⚠️ ВАЖНО: База данных

**Vercel Serverless Functions НЕ поддерживают локальную БД!**

Необходимо использовать внешнюю БД:

### Варианты:

1. **Supabase** (рекомендуется)
   - Бесплатный план: 500 MB БД
   - URL формат: `postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres`

2. **Neon** (serverless PostgreSQL)
   - Бесплатный план доступен
   - Автоматическое масштабирование

3. **Railway**
   - Простой деплой PostgreSQL
   - $5/месяц за БД

4. **AWS RDS**
   - Для production
   - Полный контроль

---

## 📝 Как добавить переменные в Vercel

### Через Dashboard:
1. Откройте проект в Vercel Dashboard
2. Settings → Environment Variables
3. Добавьте каждую переменную
4. Выберите окружения (Production, Preview, Development)

### Через CLI:
```bash
vercel env add DATABASE_URL production
vercel env add OPENAI_API_KEY production
vercel env add SECRET_KEY production
# ... и так далее для всех переменных
```

---

## ✅ Проверка после добавления

После добавления переменных, перезапустите деплой:
```bash
vercel --prod
```

Или через Dashboard: Deployments → Redeploy

---

**Не забудьте:** Обновить `DATABASE_URL` на внешнюю БД перед деплоем!

