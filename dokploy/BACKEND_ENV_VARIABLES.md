# 🔧 Переменные окружения для Backend (neiromatrius app)

**Сервис:** Backend (FastAPI)  
**Docker Compose:** `dokploy/docker-compose.backend.yml`  
**Команда запуска:** `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4`

---

## 📋 Обязательные переменные

### 1. База данных (Supabase)

**Вариант 1A: Supabase внутри Docker сети (локальный)**

```bash
# Пользователь БД
SUPABASE_USER=postgres

# Пароль БД (может быть пустым, если не требуется)
SUPABASE_PASSWORD=your-db-password

# Имя сервиса БД в Docker сети (если пусто, используется "db" по умолчанию)
SUPABASE_HOST=db
# Или оставьте пустым:
# SUPABASE_HOST=

# Порт БД (ОБЯЗАТЕЛЬНО 5437 для self-hosted Supabase!)
SUPABASE_PORT=5437

# Имя базы данных
SUPABASE_DB=postgres

# Логирование SQL запросов (true/false)
DATABASE_ECHO=false
```

**Вариант 1B: Supabase на внешнем хосте (production)**

```bash
# Пользователь БД
SUPABASE_USER=postgres

# Пароль БД (ОБЯЗАТЕЛЬНО для внешнего подключения!)
SUPABASE_PASSWORD=your-db-password

# Внешний хост Supabase
SUPABASE_HOST=supabase.dev.neiromatrius.zerocoder.pro

# Порт БД (ОБЯЗАТЕЛЬНО 5437 для self-hosted Supabase!)
SUPABASE_PORT=5437

# Имя базы данных
SUPABASE_DB=postgres

# Логирование SQL запросов (true/false)
DATABASE_ECHO=false
```

**Вариант 2: DATABASE_URL напрямую (альтернатива)**

Для локального Supabase:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5437/postgres
```

Для внешнего Supabase:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@supabase.dev.neiromatrius.zerocoder.pro:5437/postgres
```

**Вариант 3: REST API (опционально, если используете REST API)**

```bash
SUPABASE_URL=http://kong:8000
SUPABASE_REST_URL=http://kong:8000/rest/v1
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

### 2. OpenAI / LLM

```bash
OPENAI_API_KEY=sk-xxxxx
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
OPENAI_MODEL=gpt-4o-mini
```

### 3. Безопасность

```bash
# ⚠️ ОБЯЗАТЕЛЬНО: Сгенерируйте уникальный секретный ключ!
# Можно использовать: openssl rand -hex 32
SECRET_KEY=your-secret-key-here-change-in-production-min-32-chars

# CORS origins (JSON array или через запятую)
ALLOWED_ORIGINS=["https://your-frontend-domain.com","https://admin.your-domain.com"]
```

---

## 🔴 Опциональные переменные (с значениями по умолчанию)

### Redis

```bash
# Для Redis сервиса в Dokploy:
REDIS_URL=redis://neiromatrius-redis:6379/0

# Для внешнего Redis:
# REDIS_URL=redis://:password@your-redis-host:6379/0

# Без Redis (не рекомендуется для production):
# REDIS_URL=
```

### Конфигурация приложения

```bash
APP_NAME=AI Customer Support
APP_VERSION=1.0.0
DEBUG=false  # Для production установите false
LOG_LEVEL=INFO
```

### AI настройки

```bash
AI_CLASSIFICATION_TIMEOUT=30
AI_CONFIDENCE_THRESHOLD=0.85
```

### Rate Limiting

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_MESSAGE_PER_MINUTE=10
```

### Задержки доставки сообщений

```bash
RESPONSE_DELAY_SECONDS=3.0
FAREWELL_DELAY_SECONDS=10.0
DELAYS_ENABLED=true
MESSAGE_DELIVERY_DELAY_SECONDS=0
```

### Telegram Bot (опционально)

```bash
# Получите токен у @BotFather в Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ENABLED=false  # Установите true для включения бота

# Webhook настройки (для production)
TELEGRAM_WEBHOOK_URL=https://your-backend-domain.com/api/integrations/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret_here
TELEGRAM_WEBHOOK_BASE_URL=https://your-backend-domain.com
```

### Docker настройки

```bash
# Устанавливается автоматически в docker-compose файлах
DOCKER_ENV=true
```

---

## 📝 Минимальный набор для запуска

**Для локального Supabase (внутри Docker сети):**

```bash
# Database
SUPABASE_USER=postgres
SUPABASE_PASSWORD=your-password
SUPABASE_HOST=db  # или оставьте пустым для значения по умолчанию
SUPABASE_PORT=5437
SUPABASE_DB=postgres

# OpenAI
OPENAI_API_KEY=sk-xxxxx

# Security
SECRET_KEY=your-secret-key-min-32-chars
ALLOWED_ORIGINS=["https://your-frontend-domain.com"]
```

**Для внешнего Supabase (production):**

```bash
# Database
SUPABASE_USER=postgres
SUPABASE_PASSWORD=your-password  # ⚠️ ОБЯЗАТЕЛЬНО для внешнего подключения!
SUPABASE_HOST=supabase.dev.neiromatrius.zerocoder.pro  # ⚠️ Внешний хост
SUPABASE_PORT=5437
SUPABASE_DB=postgres

# OpenAI
OPENAI_API_KEY=sk-xxxxx

# Security
SECRET_KEY=your-secret-key-min-32-chars
ALLOWED_ORIGINS=["https://your-frontend-domain.com"]
```

**Рекомендуется добавить:**

```bash
# Redis
# Если Redis в том же Dokploy проекте, используйте имя сервиса:
REDIS_URL=redis://redis:6379/0
# Если Redis на другом сервисе, используйте полный URL:
# REDIS_URL=redis://your-redis-host:6379/0

# App
DEBUG=false
LOG_LEVEL=INFO
```

---

## 🔒 Безопасность

**Храните в Secrets Dokploy (не в обычных переменных):**

- `SECRET_KEY` ⚠️
- `OPENAI_API_KEY` ⚠️
- `TELEGRAM_BOT_TOKEN` ⚠️
- `TELEGRAM_WEBHOOK_SECRET` ⚠️
- `SUPABASE_SERVICE_KEY` ⚠️
- `SUPABASE_PASSWORD` ⚠️ (пароль PostgreSQL, **обязателен** для внешнего Supabase!)
- `DATABASE_URL` (если содержит пароль) ⚠️

**Важные примечания:**

- **`SUPABASE_HOST`**: 
  - Для локального Supabase (внутри Docker сети): используйте `db` или оставьте пустым (будет использовано значение по умолчанию `"db"`)
  - Для внешнего Supabase (production): укажите полный домен, например `supabase.dev.neiromatrius.zerocoder.pro`
  
- **`SUPABASE_PASSWORD`**: 
  - Для внешнего Supabase **обязателен** (без него подключение не будет работать)
  - Для локального Supabase может быть пустым, если настройки БД разрешают подключение без пароля

---

## ✅ Проверка после настройки

1. **Проверьте логи backend:**
   ```
   ✅ Redis cache connected (если Redis настроен)
   ✅ Database migrations should be executed via Supabase SQL Editor
   🚀 Starting Neiromatrius Backend...
   ```

2. **Health check:**
   ```bash
   curl http://your-backend-domain:8000/health
   ```

3. **Проверьте подключение к БД:**
   ```bash
   curl http://your-backend-domain:8000/api/monitoring/stats
   ```

---

**Дата:** 9 декабря 2025

