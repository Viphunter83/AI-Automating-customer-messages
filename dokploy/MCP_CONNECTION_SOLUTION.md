# 🔧 Решение проблемы подключения MCP к Supabase БД

**Дата:** 8 декабря 2025  
**Проблема:** `Failed to connect pg pool: Tenant or user not found (XX000)`

---

## 🔍 Диагностика проблемы

### Ошибка
```
Failed to connect pg pool: Tenant or user not found (код XX000)
```

### Причина
Прямое подключение к PostgreSQL недоступно снаружи. Supabase Gateway блокирует прямое подключение к БД через внешний хост.

### Проверенные варианты
- ❌ Порт 5437: Tenant or user not found
- ❌ Порт 5432: Tenant or user not found
- ❌ Внешний хост: не работает
- ❌ Внутренний хост: не доступен (MCP запускается локально)

---

## ✅ Решение

### Вариант 1: MCP через REST API (РЕКОМЕНДУЕТСЯ)

**Преимущества:**
- Не требует прямого доступа к PostgreSQL
- Работает через Supabase Gateway
- Безопаснее (через API Gateway)

**Шаги:**

1. **Создать функцию `execute_sql` через Supabase SQL Editor:**
   ```sql
   CREATE OR REPLACE FUNCTION public.execute_sql(query text, read_only boolean DEFAULT false)
   RETURNS jsonb
   LANGUAGE plpgsql
   AS $$
   DECLARE
     result jsonb;
   BEGIN
     EXECUTE 'SELECT COALESCE(jsonb_agg(t), ''[]''::jsonb) FROM (' || query || ') t' INTO result;
     RETURN result;
   EXCEPTION
     WHEN others THEN
       RAISE EXCEPTION 'Error executing SQL (SQLSTATE: %): % ', SQLSTATE, SQLERRM;
   END;
   $$;
   
   GRANT EXECUTE ON FUNCTION public.execute_sql(text, boolean) TO authenticated;
   GRANT EXECUTE ON FUNCTION public.execute_sql(text, boolean) TO anon;
   GRANT EXECUTE ON FUNCTION public.execute_sql(text, boolean) TO service_role;
   ```

2. **Обновить `.cursor/mcp.json` (убран `--db-url`):**
   ```json
   {
     "mcpServers": {
       "selfhosted-supabase-neiromatrius": {
         "command": "node",
         "args": [
           "/path/to/mcp-servers/selfhosted-supabase-mcp/dist/index.js",
           "--url",
           "http://supabase.dev.neiromatrius.zerocoder.pro:8000",
           "--anon-key",
           "YOUR_ANON_KEY",
           "--service-key",
           "YOUR_SERVICE_KEY",
           "--jwt-secret",
           "YOUR_JWT_SECRET"
         ]
       }
     }
   }
   ```

3. **Перезапустить Cursor**

**Работающие инструменты:**
- ✅ `list_tables` - список таблиц
- ✅ `execute_sql` - выполнение SQL через RPC
- ✅ `get_project_url` - URL проекта
- ✅ `generate_typescript_types` - генерация типов
- ✅ `list_storage_buckets` - список бакетов

**Не работающие инструменты (требуют прямого подключения):**
- ❌ `apply_migration` - применение миграций
- ❌ `list_extensions` - список расширений
- ❌ `get_database_stats` - статистика БД
- ❌ `list_auth_users` - список пользователей Auth

---

### Вариант 2: Настроить прямой доступ к PostgreSQL в Dokploy

**Требования:**
- Доступ к настройкам Supabase в Dokploy
- Возможность открыть порт PostgreSQL наружу
- Настройка firewall/security groups

**Шаги:**

1. **В Dokploy → Supabase Service:**
   - Откройте настройки портов
   - Добавьте маппинг порта PostgreSQL (например, `5432:5432`)
   - Убедитесь, что порт доступен извне

2. **Обновите `.cursor/mcp.json` с правильным портом:**
   ```json
   {
     "mcpServers": {
       "selfhosted-supabase-neiromatrius": {
         "command": "node",
         "args": [
           "/path/to/mcp-servers/selfhosted-supabase-mcp/dist/index.js",
           "--url",
           "http://supabase.dev.neiromatrius.zerocoder.pro:8000",
           "--anon-key",
           "YOUR_ANON_KEY",
           "--service-key",
           "YOUR_SERVICE_KEY",
           "--db-url",
           "postgresql://postgres:PASSWORD@supabase.dev.neiromatrius.zerocoder.pro:5432/postgres",
           "--jwt-secret",
           "YOUR_JWT_SECRET"
         ]
       }
     }
   }
   ```

**⚠️ Внимание:** Открытие порта PostgreSQL наружу может быть небезопасно. Используйте только если необходимо.

---

### Вариант 3: Использовать Supabase SQL Editor для миграций

**Для миграций:**
- Используйте **Supabase SQL Editor** (самый надежный способ)
- Скопируйте SQL из `database/migrations_supabase.sql`
- Выполните через SQL Editor

**Для работы с данными:**
- Используйте MCP через REST API (после создания функции `execute_sql`)

---

## 📋 Итоговая рекомендация

1. **Для миграций:** Используйте **Supabase SQL Editor**
2. **Для работы с данными:** Используйте **MCP через REST API** (Вариант 1)
3. **Для полного функционала:** Настройте прямой доступ к PostgreSQL (Вариант 2)

---

## 📁 Созданные файлы

- ✅ `dokploy/MCP_WITHOUT_DIRECT_DB.md` - инструкция по работе через REST API
- ✅ `dokploy/MCP_CONNECTION_FIX.md` - альтернативные решения
- ✅ `.cursor/mcp.json` - обновлена конфигурация (убран `--db-url`)

---

## 🔗 Полезные ссылки

- [Supabase Self-Hosting Docs](https://supabase.com/docs/guides/self-hosting)
- [MCP Server Documentation](https://github.com/HenkDz/selfhosted-supabase-mcp)

---

**Дата:** 8 декабря 2025






