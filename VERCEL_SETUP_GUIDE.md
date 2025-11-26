# 🚀 Руководство по деплою на Vercel

**Дата:** 2025-11-26

---

## ✅ Подготовка завершена

Созданы все необходимые файлы для деплоя FastAPI бэкенда на Vercel:

1. ✅ `vercel.json` - Конфигурация проекта
2. ✅ `api/index.py` - Serverless функция для FastAPI
3. ✅ `requirements.txt` - Python зависимости
4. ✅ `.vercelignore` - Исключения для деплоя

---

## 📋 Шаги деплоя

### Шаг 1: Установка Vercel CLI (если еще не установлен)

```bash
npm i -g vercel
```

### Шаг 2: Вход в аккаунт Vercel

```bash
vercel login
```

### Шаг 3: Инициализация проекта (первый раз)

```bash
vercel
```

Следуйте инструкциям:
- Выберите команду (team) или личный аккаунт
- Выберите существующий проект или создайте новый
- Подтвердите настройки

### Шаг 4: Настройка переменных окружения

После инициализации проекта, настройте переменные окружения в Vercel Dashboard или через CLI:

```bash
# Обязательные переменные
vercel env add DATABASE_URL production
vercel env add OPENAI_API_KEY production
vercel env add SECRET_KEY production

# Опциональные переменные
vercel env add OPENAI_API_BASE production
vercel env add OPENAI_MODEL production
vercel env add DEBUG production
vercel env add LOG_LEVEL production
vercel env add ALLOWED_ORIGINS production
```

**Или через Dashboard:**
1. Откройте проект в Vercel Dashboard
2. Перейдите в Settings → Environment Variables
3. Добавьте все переменные из `backend/.env`

### Шаг 5: Деплой

```bash
# Preview deployment
vercel

# Production deployment
vercel --prod
```

---

## 🔧 Альтернатива: Деплой через Git

Если у вас подключен Git репозиторий:

1. Закоммитьте изменения:
   ```bash
   git add .
   git commit -m "Add Vercel configuration"
   git push
   ```

2. В Vercel Dashboard:
   - Settings → Git
   - Подключите репозиторий
   - Автоматические деплои будут запускаться при push

---

## ⚠️ Важные замечания

### База данных

**КРИТИЧНО:** Vercel Serverless Functions не поддерживают локальную БД!

Необходимо использовать внешнюю БД:
- **Supabase** (рекомендуется) - бесплатный план доступен
- **Neon** - serverless PostgreSQL
- **Railway** - простой деплой PostgreSQL
- **AWS RDS** - для production

**Обновите `DATABASE_URL`** на внешнюю БД перед деплоем!

### WebSocket

- WebSocket endpoints (`/ws`) **не будут работать** на Vercel
- Используйте Vercel Realtime или внешний сервис для WebSocket

### Scheduler (APScheduler)

- APScheduler **не работает** на serverless функциях
- Используйте **Vercel Cron Jobs** для периодических задач

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

### Файловая система

- Serverless функции имеют **read-only** файловую систему
- Не сохраняйте файлы локально
- Используйте внешнее хранилище (S3, Supabase Storage)

---

## 📝 Переменные окружения для Vercel

### Обязательные

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
OPENAI_API_KEY=sk-...
SECRET_KEY=your-secret-key-min-32-chars
```

### Опциональные

```bash
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
OPENAI_MODEL=gpt-4o-mini
DEBUG=False
LOG_LEVEL=INFO
ALLOWED_ORIGINS=["https://your-frontend.vercel.app"]
```

---

## 🧪 Проверка после деплоя

После успешного деплоя проверьте:

1. **Health check:**
   ```bash
   curl https://your-project.vercel.app/health
   ```

2. **API docs:**
   ```
   https://your-project.vercel.app/docs
   ```

3. **Создание сообщения:**
   ```bash
   curl -X POST https://your-project.vercel.app/api/messages/ \
     -H "Content-Type: application/json" \
     -d '{"client_id": "test", "content": "Привет"}'
   ```

---

## 🎯 Следующие шаги

1. ✅ Настроить внешнюю БД (Supabase/Neon)
2. ✅ Обновить `DATABASE_URL` в переменных окружения Vercel
3. ✅ Задеплоить проект
4. ⚠️ Настроить Cron Jobs для scheduler
5. ⚠️ Настроить WebSocket альтернативу (если нужно)

---

## 📚 Дополнительная информация

- [Vercel Python Runtime](https://vercel.com/docs/functions/runtimes/python)
- [Vercel Cron Jobs](https://vercel.com/docs/cron-jobs)
- [FastAPI на Vercel](https://vercel.com/docs/frameworks/backend/fastapi)

---

**Готово к деплою!** 🚀

