# 🔌 Настройка MCP для Self-Hosted Supabase

**Проект:** Neiromatrius  
**Self-Hosted Supabase:** supabase.dev.neiromatrius.zerocoder.pro

---

## ✅ Вы правы! MCP можно использовать с self-hosted Supabase

Для self-hosted Supabase есть несколько вариантов использования MCP:

---

## 📋 Вариант 1: Сторонний MCP сервер (HenkDz/selfhosted-supabase-mcp)

### Установка и настройка

```bash
# Клонировать репозиторий
git clone https://github.com/HenkDz/selfhosted-supabase-mcp.git
cd selfhosted-supabase-mcp

# Установить зависимости
npm install

# Настроить переменные окружения
export SUPABASE_URL=http://supabase.dev.neiromatrius.zerocoder.pro:8000
export SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjUyMDIwNTgsImV4cCI6MTg5MzQ1NjAwMCwicm9sZSI6ImFub24iLCJpc3MiOiJzdXBhYmFzZSJ9.aePmG2KknrQ8ofJdtvnQbhg0S8lEj8NLqsNsvOojucQ
export SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjUyMDIwNTgsImV4cCI6MTg5MzQ1NjAwMCwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlzcyI6InN1cGFiYXNlIn0.-aJYZ-S4pFaAHbZXUYGRkZ6uQQDWyldU8NMBjOjjLsI

# Запустить MCP сервер
npm start
```

### Подключение в Cursor

В настройках Cursor добавьте MCP сервер:

```json
{
  "mcpServers": {
    "supabase-selfhosted": {
      "command": "node",
      "args": ["/path/to/selfhosted-supabase-mcp/index.js"],
      "env": {
        "SUPABASE_URL": "http://supabase.dev.neiromatrius.zerocoder.pro:8000",
        "SUPABASE_ANON_KEY": "your_anon_key",
        "SUPABASE_SERVICE_ROLE_KEY": "your_service_role_key"
      }
    }
  }
}
```

---

## 📋 Вариант 2: Через Docker контейнер (если есть доступ)

Если у вас есть доступ к серверу Dokploy, можно выполнить миграции напрямую в контейнере:

```bash
# Выполнить SQL в контейнере PostgreSQL
docker exec -i neiromatrius-supabase-ckjmxl-supabase-db-1 \
  psql -U postgres -d postgres < database/migrations_supabase.sql
```

Или через Docker Compose:

```bash
cd /path/to/supabase/docker-compose
docker-compose exec db psql -U postgres -d postgres < /path/to/migrations_supabase.sql
```

---

## 📋 Вариант 3: Через Supabase SQL Editor (самый простой)

1. Откройте: **http://supabase.dev.neiromatrius.zerocoder.pro**
2. Войдите:
   - Username: `supabase`
   - Password: `ld1jah8qk5sigutjplm1n80dvn5jjjbz`
3. Откройте **SQL Editor**
4. Скопируйте код из `database/migrations_supabase.sql`
5. Вставьте и нажмите **Run**

---

## 📋 Вариант 4: Через Supabase CLI (если настроен локально)

Если у вас настроен Supabase CLI для self-hosted:

```bash
# Выполнить миграции через CLI
supabase db push --db-url "postgresql://postgres:tqwe8vpzjxptmged6w8v6cxm30fedpqg@supabase.dev.neiromatrius.zerocoder.pro:5437/postgres"
```

---

## 🔧 Настройка MCP в Cursor для Self-Hosted

### Шаг 1: Установите MCP сервер

Выберите один из вариантов:
- **HenkDz/selfhosted-supabase-mcp** (простой)
- **Apify/supabase-mcp-selfhosted** (продакшн-ready)

### Шаг 2: Настройте переменные окружения

```bash
export SUPABASE_URL=http://supabase.dev.neiromatrius.zerocoder.pro:8000
export SUPABASE_ANON_KEY=your_anon_key
export SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Шаг 3: Добавьте в Cursor MCP конфигурацию

Откройте настройки Cursor и добавьте MCP сервер.

---

## ✅ Рекомендация

**Для быстрого выполнения миграций сейчас:**
- Используйте **Вариант 3** (Supabase SQL Editor) - самый простой и надежный

**Для долгосрочного использования:**
- Настройте **Вариант 1** (MCP сервер) для удобной работы через Cursor

---

**Дата:** 8 декабря 2025







