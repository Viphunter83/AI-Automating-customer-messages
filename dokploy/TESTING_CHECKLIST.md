# ✅ Чеклист тестирования перед деплоем

**Проект:** Neiromatrius  
**Дата:** 8 декабря 2025

---

## 🔍 Проверка конфигурации БД

### Текущая реализация

**Важно:** Система использует **прямое подключение к PostgreSQL** через SQLAlchemy ORM, а не Supabase REST API.

**Причина:** 
- SQLAlchemy ORM обеспечивает типобезопасность и удобство работы
- Прямое подключение быстрее REST API
- Supabase self-hosted поддерживает прямое PostgreSQL подключение

### Настройка подключения

**Формат DATABASE_URL для Supabase:**
```bash
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@[SUPABASE_HOST]:[PORT]/postgres
```

**Где взять параметры:**
1. В Supabase Dashboard → **Settings** → **Database**
2. Найдите **Connection String** (PostgreSQL)
3. Добавьте `+asyncpg` после `postgresql`: `postgresql+asyncpg://...`

---

## ✅ Чеклист проверки перед деплоем

### 1. База данных

- [ ] Supabase self-hosted установлен и работает
- [ ] Миграции выполнены (`database/migrations_supabase.sql`)
- [ ] DATABASE_URL получен из Supabase Dashboard
- [ ] Формат DATABASE_URL правильный: `postgresql+asyncpg://...`
- [ ] Пароль в DATABASE_URL правильный
- [ ] Хост доступен из Dokploy сервера
- [ ] Порт правильный (обычно 5432)
- [ ] База данных `postgres` существует

### 2. Переменные окружения Backend

- [ ] `DATABASE_URL` - строка подключения к Supabase PostgreSQL
- [ ] `OPENAI_API_KEY` - ключ OpenAI API
- [ ] `SECRET_KEY` - секретный ключ (минимум 32 символа)
- [ ] `ALLOWED_ORIGINS` - CORS origins (JSON array или comma-separated)
- [ ] `REDIS_URL` - если используется Redis
- [ ] `TELEGRAM_BOT_TOKEN` - если используется Telegram
- [ ] `TELEGRAM_ENABLED` - true/false

### 3. Переменные окружения Frontend

- [ ] `NEXT_PUBLIC_API_URL` - URL API (обычно `/api`)
- [ ] `BACKEND_API_URL` - внутренний URL backend

### 4. Docker Compose файлы

- [ ] `dokploy/docker-compose.backend.yml` - проверен
- [ ] `dokploy/docker-compose.frontend.yml` - проверен
- [ ] `dokploy/docker-compose.redis.yml` - если используется Redis
- [ ] Все переменные используют `${VAR}` синтаксис
- [ ] Health checks настроены
- [ ] Networks настроены правильно

### 5. Тестирование подключения

#### Локальное тестирование (перед деплоем)

```bash
# 1. Проверка DATABASE_URL формата
python3 -c "
import os
url = os.getenv('DATABASE_URL', '')
if '+asyncpg' not in url:
    print('❌ ERROR: DATABASE_URL должен содержать +asyncpg')
    print(f'Текущий: {url}')
    exit(1)
if 'postgresql' not in url:
    print('❌ ERROR: DATABASE_URL должен начинаться с postgresql')
    exit(1)
print('✅ DATABASE_URL формат правильный')
"

# 2. Тест подключения к БД
python3 << 'EOF'
import asyncio
import asyncpg
import os

async def test_db():
    url = os.getenv('DATABASE_URL', '')
    if not url:
        print('❌ DATABASE_URL не установлен')
        return
    
    # Убираем +asyncpg для asyncpg.connect
    url = url.replace('+asyncpg', '')
    
    try:
        conn = await asyncpg.connect(url)
        result = await conn.fetchval('SELECT 1')
        print(f'✅ Подключение к БД успешно: {result}')
        await conn.close()
    except Exception as e:
        print(f'❌ Ошибка подключения к БД: {e}')
        return False
    return True

asyncio.run(test_db())
EOF
```

---

## 🧪 Тестирование после деплоя

### 1. Health Checks

```bash
# Backend health
curl https://api.your-domain.com/health

# Должен вернуть:
# {"status":"ok","database":"ok","redis":"ok|unavailable"}

# Database health
curl https://api.your-domain.com/api/health/db

# Должен вернуть:
# {"status":"ok","database":"connected"}
```

### 2. Тест API

```bash
# Отправка тестового сообщения
curl -X POST https://api.your-domain.com/api/messages/ \
  -H "Content-Type: application/json" \
  -H "X-Webhook-URL: https://test-webhook.com/test" \
  -H "X-Platform: test" \
  -H "X-Chat-ID: test-123" \
  -d '{
    "client_id": "test_client_001",
    "content": "Привет! Тестовое сообщение"
  }'

# Должен вернуть ответ с classification и response
```

### 3. Проверка логов

В Dokploy для каждого сервиса проверьте логи:

**Backend должен показать:**
```
✅ Database connection established and responsive
✅ Redis cache connected (или ⚠️ Redis cache unavailable, using in-memory fallback)
🚀 Starting up application...
```

**Frontend должен показать:**
```
✓ Ready in Xms
```

---

## 🔧 Исправление проблем

### Проблема: Database connection failed

**Причины:**
1. Неправильный DATABASE_URL формат
2. Неправильный пароль
3. Хост недоступен
4. Firewall блокирует подключение

**Решение:**
1. Проверьте DATABASE_URL формат: `postgresql+asyncpg://postgres:password@host:5432/postgres`
2. Проверьте пароль в Supabase Dashboard
3. Убедитесь, что Supabase доступен из Dokploy сервера
4. Проверьте firewall правила

### Проблема: Redis connection failed

**Решение:**
- Это нормально, если Redis не используется
- Система автоматически использует in-memory cache
- Для production рекомендуется настроить Redis

### Проблема: Frontend не подключается к Backend

**Решение:**
1. Проверьте `BACKEND_API_URL` и `NEXT_PUBLIC_API_URL`
2. Убедитесь, что оба сервиса в одной сети Docker
3. Проверьте CORS настройки (`ALLOWED_ORIGINS`)

---

## 📋 Финальный чеклист перед пушем в GitHub

- [ ] Все файлы проверены
- [ ] DATABASE_URL формат правильный
- [ ] Переменные окружения документированы
- [ ] Docker Compose файлы проверены
- [ ] Health checks настроены
- [ ] Логи проверены на ошибки
- [ ] Тесты пройдены (если есть)

---

**Дата создания:** 8 декабря 2025







