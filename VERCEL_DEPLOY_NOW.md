# 🚀 Деплой на Vercel - Пошаговая инструкция

**Дата:** 2025-11-27  
**Статус:** Railway успешно задеплоен ✅

---

## 📋 Подготовка

### Шаг 1: Получите DATABASE_URL из Railway

1. Откройте Railway Dashboard
2. PostgreSQL сервис → Variables
3. Скопируйте `DATABASE_URL` или `POSTGRES_URL`
4. **Измените формат:** `postgresql://` → `postgresql+asyncpg://`

---

## 🚀 Деплой на Vercel

### Шаг 1: Инициализация проекта

```bash
cd /Users/apple/AI\ Automating\ customer\ messages
vercel
```

**Ответьте на вопросы:**
- Set up and deploy? → `Y`
- Which scope? → Выберите `team_ckk1yHJodr9A9k87ScdWHwmQ` (Oleg's projects)
- Link to existing project? → `N` (создать новый)
- Project name? → `ai-customer-support-backend`
- Directory? → `.`
- Override settings? → `N`

### Шаг 2: Настройка переменных окружения

После инициализации настройте переменные в Vercel Dashboard:

1. Откройте [vercel.com/dashboard](https://vercel.com/dashboard)
2. Найдите проект `ai-customer-support-backend`
3. Settings → Environment Variables
4. Добавьте переменные:

**Обязательные:**
```
DATABASE_URL = postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway
OPENAI_API_KEY = sk-your-api-key-here
SECRET_KEY = your-secret-key-minimum-32-characters-long
```

**Опциональные:**
```
OPENAI_API_BASE = https://api.proxyapi.ru/openai/v1
OPENAI_MODEL = gpt-4o-mini
DEBUG = False
LOG_LEVEL = INFO
```

**Важно:** Выберите окружения: ✅ Production, ✅ Preview, ✅ Development

### Шаг 3: Production деплой

```bash
vercel --prod
```

---

## ✅ Проверка после деплоя

```bash
# Health check
curl https://your-project.vercel.app/health

# API docs
open https://your-project.vercel.app/docs
```

---

**Готово!** После деплоя ваш FastAPI бэкенд будет доступен на Vercel! 🚀

