# ✅ Решение: MCP без прямого подключения к PostgreSQL

**Проблема:** Прямое подключение к PostgreSQL недоступно снаружи (ошибка "Tenant or user not found")

**Решение:** Использовать MCP через Supabase REST API без прямого подключения к БД

---

## 🔧 Шаг 1: Создать функцию execute_sql через SQL Editor

1. **Откройте Supabase SQL Editor**
2. **Выполните следующий SQL:**

```sql
-- Создать функцию execute_sql для выполнения SQL через RPC
CREATE OR REPLACE FUNCTION public.execute_sql(query text, read_only boolean DEFAULT false)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
  result jsonb;
BEGIN
  -- Execute the dynamic query and aggregate results into a JSONB array
  EXECUTE 'SELECT COALESCE(jsonb_agg(t), ''[]''::jsonb) FROM (' || query || ') t' INTO result;
  RETURN result;
EXCEPTION
  WHEN others THEN
    -- Rethrow the error with context, including the original SQLSTATE
    RAISE EXCEPTION 'Error executing SQL (SQLSTATE: %): % ', SQLSTATE, SQLERRM;
END;
$$;

-- Предоставить права на выполнение функции
GRANT EXECUTE ON FUNCTION public.execute_sql(text, boolean) TO authenticated;
GRANT EXECUTE ON FUNCTION public.execute_sql(text, boolean) TO anon;
GRANT EXECUTE ON FUNCTION public.execute_sql(text, boolean) TO service_role;
```

3. **Проверьте создание функции:**

```sql
SELECT proname, proargtypes 
FROM pg_proc 
WHERE proname = 'execute_sql';
```

---

## 🔧 Шаг 2: Обновить конфигурацию MCP (убрать --db-url)

**Обновите `.cursor/mcp.json`:**

```json
{
  "mcpServers": {
    "selfhosted-supabase-neiromatrius": {
      "command": "node",
      "args": [
        "/Users/apple/AI Automating customer messages /mcp-servers/selfhosted-supabase-mcp/dist/index.js",
        "--url",
        "http://supabase.dev.neiromatrius.zerocoder.pro:8000",
        "--anon-key",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjUyMDIwNTgsImV4cCI6MTg5MzQ1NjAwMCwicm9sZSI6ImFub24iLCJpc3MiOiJzdXBhYmFzZSJ9.aePmG2KknrQ8ofJdtvnQbhg0S8lEj8NLqsNsvOojucQ",
        "--service-key",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjUyMDIwNTgsImV4cCI6MTg5MzQ1NjAwMCwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlzcyI6InN1cGFiYXNlIn0.-aJYZ-S4pFaAHbZXUYGRkZ6uQQDWyldU8NMBjOjjLsI",
        "--jwt-secret",
        "bkyp6d09bswvw6u6p34ywizv9jd1gfdt"
      ]
    }
  }
}
```

**Изменения:**
- ❌ Убран `--db-url` (не нужен для работы через REST API)
- ✅ Оставлены `--url`, `--anon-key`, `--service-key`, `--jwt-secret`

---

## ✅ Шаг 3: Перезапустить Cursor и проверить

1. **Перезапустите Cursor**
2. **Попробуйте выполнить MCP команду:**

```bash
# Через MCP инструменты в Cursor
list_tables
execute_sql
```

---

## 📋 Какие инструменты будут работать

### ✅ Работают через REST API (без прямого подключения):
- `list_tables` - список таблиц
- `execute_sql` - выполнение SQL через RPC функцию
- `get_project_url` - URL проекта
- `get_anon_key` - Anon ключ
- `get_service_key` - Service Role ключ
- `generate_typescript_types` - генерация типов
- `list_storage_buckets` - список бакетов
- `list_storage_objects` - список объектов

### ❌ Требуют прямого подключения к PostgreSQL:
- `apply_migration` - применение миграций (требует транзакций)
- `list_extensions` - список расширений (требует pg_catalog)
- `get_database_connections` - активные подключения (требует pg_stat_activity)
- `get_database_stats` - статистика БД (требует pg_stat_*)
- `list_auth_users` - список пользователей Auth (требует схему auth)
- `create_auth_user` - создание пользователя (требует схему auth)
- `delete_auth_user` - удаление пользователя (требует схему auth)
- `update_auth_user` - обновление пользователя (требует схему auth)

---

## 🎯 Рекомендация

**Для миграций:**
- Используйте **Supabase SQL Editor** (самый надежный способ)

**Для работы с данными:**
- Используйте **MCP через REST API** (после создания функции `execute_sql`)

---

## 🔍 Проверка работы

После создания функции `execute_sql` и обновления конфигурации:

1. **Проверьте подключение MCP:**
   ```bash
   # В Cursor попробуйте:
   list_tables
   ```

2. **Проверьте выполнение SQL:**
   ```bash
   # В Cursor попробуйте:
   execute_sql: SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5;
   ```

---

**Дата:** 8 декабря 2025

