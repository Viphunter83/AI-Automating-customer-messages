# ✅ MCP Сервер для Self-Hosted Supabase - Настроен

**Проект:** Neiromatrius  
**Дата:** 8 декабря 2025

---

## ✅ Что было сделано

1. ✅ Установлен MCP сервер `HenkDz/selfhosted-supabase-mcp`
2. ✅ Собран проект (TypeScript → JavaScript)
3. ✅ Создана конфигурация для Cursor (`.cursor/mcp.json`)
4. ✅ Настроены все необходимые параметры подключения

---

## 📁 Структура файлов

```
mcp-servers/
└── selfhosted-supabase-mcp/
    ├── dist/
    │   └── index.js          # Скомпилированный MCP сервер
    ├── src/                   # Исходный код
    └── package.json

.cursor/
└── mcp.json                   # Конфигурация для Cursor
```

---

## 🔧 Конфигурация

Файл `.cursor/mcp.json` содержит:

- **SUPABASE_URL:** `http://supabase.dev.neiromatrius.zerocoder.pro:8000`
- **ANON_KEY:** настроен
- **SERVICE_ROLE_KEY:** настроен
- **DATABASE_URL:** `postgresql://postgres:...@supabase.dev.neiromatrius.zerocoder.pro:5437/postgres`
- **JWT_SECRET:** настроен

---

## 🚀 Использование

### Шаг 1: Перезапустите Cursor

После создания конфигурации перезапустите Cursor, чтобы MCP сервер подключился.

### Шаг 2: Проверьте подключение

После перезапуска Cursor должен автоматически подключиться к MCP серверу. Вы можете использовать MCP инструменты для работы с базой данных.

### Шаг 3: Выполните миграции

Теперь можно выполнить миграции через MCP:

```sql
-- Через MCP инструмент execute_sql
-- Или через apply_migration для применения миграций
```

---

## 📋 Доступные MCP инструменты

После подключения доступны следующие инструменты:

### Schema & Migrations
- `list_tables` - список таблиц
- `list_extensions` - список расширений PostgreSQL
- `list_migrations` - список примененных миграций
- `apply_migration` - применение SQL миграции

### Database Operations
- `execute_sql` - выполнение SQL запросов
- `get_database_connections` - активные подключения
- `get_database_stats` - статистика базы данных

### Project Configuration
- `get_project_url` - URL проекта
- `get_anon_key` - Anon ключ
- `get_service_key` - Service Role ключ
- `verify_jwt_secret` - проверка JWT секрета

### Development Tools
- `generate_typescript_types` - генерация TypeScript типов
- `rebuild_hooks` - перезапуск pg_net worker

### Auth User Management
- `list_auth_users` - список пользователей
- `get_auth_user` - получение пользователя
- `create_auth_user` - создание пользователя
- `delete_auth_user` - удаление пользователя
- `update_auth_user` - обновление пользователя

### Storage
- `list_storage_buckets` - список бакетов
- `list_storage_objects` - список объектов

### Realtime
- `list_realtime_publications` - список публикаций

---

## 🔄 Использование для других проектов

### Вариант 1: Использовать тот же MCP сервер с другой конфигурацией

Создайте отдельную конфигурацию в `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "selfhosted-supabase-project1": {
      "command": "node",
      "args": [
        "/path/to/mcp-servers/selfhosted-supabase-mcp/dist/index.js",
        "--url", "http://project1.example.com:8000",
        "--anon-key", "your-anon-key",
        "--service-key", "your-service-key",
        "--db-url", "postgresql://...",
        "--jwt-secret", "your-jwt-secret"
      ]
    },
    "selfhosted-supabase-project2": {
      "command": "node",
      "args": [
        "/path/to/mcp-servers/selfhosted-supabase-mcp/dist/index.js",
        "--url", "http://project2.example.com:8000",
        "--anon-key", "your-anon-key-2",
        "--service-key", "your-service-key-2",
        "--db-url", "postgresql://...",
        "--jwt-secret", "your-jwt-secret-2"
      ]
    }
  }
}
```

### Вариант 2: Создать универсальный скрипт запуска

Создайте скрипт `mcp-servers/start-mcp.sh`:

```bash
#!/bin/bash
# Использование: ./start-mcp.sh <project-name> <supabase-url> <anon-key> <service-key> <db-url> <jwt-secret>

PROJECT_NAME=$1
SUPABASE_URL=$2
ANON_KEY=$3
SERVICE_KEY=$4
DB_URL=$5
JWT_SECRET=$6

node mcp-servers/selfhosted-supabase-mcp/dist/index.js \
  --url "$SUPABASE_URL" \
  --anon-key "$ANON_KEY" \
  --service-key "$SERVICE_KEY" \
  --db-url "$DB_URL" \
  --jwt-secret "$JWT_SECRET"
```

---

## 🧪 Тестирование

После перезапуска Cursor проверьте доступность MCP инструментов:

1. Откройте Cursor
2. Попробуйте использовать MCP инструменты (например, `list_tables`)
3. Выполните тестовый SQL запрос через `execute_sql`

---

## 📝 Выполнение миграций через MCP

Теперь можно выполнить миграции через MCP:

1. Используйте инструмент `apply_migration` с содержимым `database/migrations_supabase.sql`
2. Или используйте `execute_sql` для выполнения SQL кода

---

## ⚠️ Важные замечания

1. **Безопасность:** Файл `.cursor/mcp.json` содержит чувствительные данные. Не коммитьте его в Git без `.gitignore`.

2. **Перезапуск:** После изменения конфигурации MCP необходимо перезапустить Cursor.

3. **Порты:** Убедитесь, что порты Supabase доступны:
   - `8000` - Kong Gateway (HTTP)
   - `5437` - PostgreSQL (если используется прямое подключение)

4. **Права доступа:** `DATABASE_URL` должен иметь права на создание функций и выполнение SQL.

---

## 🔗 Полезные ссылки

- **Репозиторий MCP сервера:** https://github.com/HenkDz/selfhosted-supabase-mcp
- **Документация MCP:** https://modelcontextprotocol.io
- **Supabase Self-Hosting:** https://supabase.com/docs/guides/self-hosting

---

**Дата:** 8 декабря 2025







