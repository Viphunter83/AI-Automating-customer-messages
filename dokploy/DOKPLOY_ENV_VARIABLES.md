# 🔐 Переменные окружения для Dokploy

**Проект:** Neiromatrius  
**Дата:** 8 декабря 2025

---

## 📋 Инструкция по настройке

1. В Dokploy перейдите в раздел **Environment Variables** для каждого сервиса
2. Добавьте переменные из соответствующих секций ниже
3. Для секретных значений используйте **Secrets** в Dokploy

---

## 🔧 Backend Service Variables

### Database (Supabase - прямое PostgreSQL подключение)

**⚠️ ВАЖНО:** Конфигурация соответствует примеру заказчика из другого проекта.

**Обязательные переменные:**

```bash
# URL Supabase API Gateway (для REST API, опционально)
# Для внутреннего доступа в Dokploy:
SUPABASE_URL=http://kong:8000

# Или для внешнего доступа:
# SUPABASE_URL=https://supabase.neiroaleksandra.dev.zerocoder.pro

# Role Key (для REST API, опционально, может быть пустым)
SUPABASE_KEY=

# Пользователь БД (обычно "postgres")
SUPABASE_USER=postgres

# Пароль БД (может быть пустым, если не требуется)
SUPABASE_PASSWORD=

# Имя сервиса БД в Docker сети (может быть пустым, тогда используется "db" по умолчанию)
SUPABASE_HOST=

# Порт БД (ОБЯЗАТЕЛЬНО 5437!)
SUPABASE_PORT=5437

# Имя базы данных (обычно "postgres")
SUPABASE_DB=postgres

# Логирование SQL запросов (true/false)
DATABASE_ECHO=true
```

**Как это работает:**

1. **Для прямого подключения к PostgreSQL:**
   - Система использует `SUPABASE_USER`, `SUPABASE_PASSWORD`, `SUPABASE_HOST`, `SUPABASE_PORT`, `SUPABASE_DB`
   - Если `SUPABASE_HOST` пустой - используется `"db"` по умолчанию
   - Если `SUPABASE_PASSWORD` пустой - подключается без пароля (если разрешено настройками БД)
   - Автоматически строится `DATABASE_URL`: `postgresql+asyncpg://postgres@db:5432/postgres`

2. **Для REST API (если нужно):**
   - `SUPABASE_URL` - адрес API Gateway (Kong или внешний URL)
   - `SUPABASE_KEY` - Role Key (опционально)

**Вариант 2: DATABASE_URL напрямую (для обратной совместимости)**

```bash
# Если хотите указать полную строку подключения:
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/postgres
```

**Проверка подключения:**
После настройки проверьте подключение:
```bash
python3 scripts/test_db_connection.py
```

### Redis (Optional, но рекомендуется для production)

**Варианты:**

**Вариант 1: Отдельный Redis сервис в Dokploy (рекомендуется)**
```bash
# После создания Redis сервиса используйте:
REDIS_URL=redis://neiromatrius-redis:6379/0
```

**Вариант 2: Внешний Redis (Redis Cloud, Upstash и т.д.)**
```bash
REDIS_URL=redis://your-redis-host:6379/0
# Или с паролем:
REDIS_URL=redis://:password@your-redis-host:6379/0
```

**Вариант 3: Без Redis (не рекомендуется для production)**
```bash
# Оставьте пустым - будет использоваться in-memory cache
# ⚠️ Внимание: при нескольких инстансах backend возможны дубликаты сообщений
REDIS_URL=
```

**Зачем нужен Redis:**
- ✅ Предотвращение дубликатов сообщений между инстансами
- ✅ Распределенное кеширование классификаций AI
- ✅ Метрики и статистика
- ✅ Улучшение производительности

### OpenAI / LLM

```bash
OPENAI_API_KEY=sk-xxxxx
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
OPENAI_MODEL=gpt-4o-mini
```

### Application Configuration

```bash
APP_NAME=Neiromatrius
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
```

### Security

```bash
# ⚠️ ВАЖНО: Сгенерируйте уникальный секретный ключ!
# Можно использовать: openssl rand -hex 32
SECRET_KEY=your-secret-key-here-change-in-production-min-32-chars

# CORS origins (JSON array или comma-separated)
ALLOWED_ORIGINS=["https://your-frontend-domain.com","https://admin.your-domain.com"]
```

### AI Configuration

```bash
AI_CLASSIFICATION_TIMEOUT=30
AI_CONFIDENCE_THRESHOLD=0.85
```

### Telegram Bot (Optional)

```bash
# Получите токен у @BotFather в Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Включить/выключить Telegram бота
TELEGRAM_ENABLED=false

# Webhook настройки (если используете webhook вместо polling)
TELEGRAM_WEBHOOK_URL=https://your-backend-domain.com/api/integrations/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret_here
TELEGRAM_WEBHOOK_BASE_URL=https://your-backend-domain.com
```

---

## 🎨 Frontend Service Variables

### Next.js Configuration

```bash
NODE_ENV=production
NEXT_PUBLIC_API_URL=/api
```

### Backend API URL

```bash
# URL backend для server-side запросов
# Используйте внутренний Docker network или внешний URL
BACKEND_API_URL=http://backend:8000

# Или если backend на другом сервисе:
# BACKEND_API_URL=https://your-backend-domain.com
```

---

## 🔄 Общие переменные для обоих сервисов

### Network Configuration

```bash
# Имя Docker network (создается автоматически Dokploy)
NETWORK_NAME=neiromatrius-network
```

---

## 📝 Примеры значений для разных окружений

### Development

```bash
DEBUG=true
LOG_LEVEL=DEBUG
NODE_ENV=development
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

### Production

```bash
DEBUG=false
LOG_LEVEL=INFO
NODE_ENV=production
ALLOWED_ORIGINS=["https://your-production-domain.com"]
```

---

## ⚠️ Важные замечания

1. **SECRET_KEY**: Обязательно измените на уникальное значение в production!
2. **DATABASE_URL**: Используйте правильный формат для Supabase PostgreSQL
3. **ALLOWED_ORIGINS**: Укажите реальные домены фронтенда
4. **TELEGRAM_BOT_TOKEN**: Храните в Secrets Dokploy, не в обычных переменных
5. **OPENAI_API_KEY**: Храните в Secrets Dokploy

---

## 🔒 Рекомендации по безопасности

- Используйте **Secrets** в Dokploy для всех чувствительных данных:
  - `SECRET_KEY`
  - `DATABASE_URL` (содержит пароль)
  - `OPENAI_API_KEY`
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_WEBHOOK_SECRET`

---

## 📚 Дополнительная информация

- [Dokploy Environment Variables Documentation](https://docs.dokploy.com/docs/core/environment-variables)
- [Supabase Connection Strings](https://supabase.com/docs/guides/database/connecting-to-postgres)

---

**Дата создания:** 8 декабря 2025

