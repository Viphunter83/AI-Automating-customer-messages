# 🔍 Диагностика проблемы MCP

**Проблема:** MCP сервер не видит функцию `execute_sql` даже после `NOTIFY pgrst, 'reload schema'` и перезапуска Cursor.

---

## 🔍 Шаг 1: Проверьте функцию в БД

Выполните в Supabase SQL Editor:

```sql
-- Проверка существования функции
SELECT 
    proname, 
    pronamespace::regnamespace as schema,
    pg_get_function_arguments(oid) as arguments
FROM pg_proc 
WHERE proname = 'execute_sql';
```

**Ожидаемый результат:**
- `proname`: `execute_sql`
- `schema`: `public`
- `arguments`: `query text, read_only boolean DEFAULT false`

---

## 🔍 Шаг 2: Проверьте права на функцию

```sql
-- Проверка прав на функцию
SELECT 
    grantee, 
    privilege_type 
FROM information_schema.routine_privileges 
WHERE routine_name = 'execute_sql'
ORDER BY grantee;
```

**Ожидаемый результат:** Права для:
- `authenticated` (EXECUTE)
- `anon` (EXECUTE)
- `service_role` (EXECUTE)

---

## 🔍 Шаг 3: Попробуйте вызвать функцию напрямую через SQL

```sql
-- Тест функции через SQL Editor
SELECT public.execute_sql('SELECT 1 as test', true);
```

**Ожидаемый результат:** `[{"test": 1}]` или похожий JSON массив

**Если ошибка:** Функция не работает, нужно пересоздать.

---

## 🔄 Шаг 4: Перезапустите PostgREST контейнер

**Критически важно:** `NOTIFY pgrst, 'reload schema'` может не сработать, если PostgREST не слушает уведомления.

### В Dokploy:

1. **Откройте Dokploy Dashboard**
2. **Найдите сервис Supabase**
3. **Найдите контейнер `postgrest`** (или `postgres-rest`, `supabase-rest`)
4. **Перезапустите контейнер:**
   - Нажмите на контейнер
   - Выберите "Restart" или "Перезапустить"
   - Дождитесь перезапуска (обычно 5-10 секунд)

### Альтернатива: Через Docker напрямую

Если у вас есть доступ к серверу:

```bash
# Найдите контейнер PostgREST
docker ps | grep postgrest

# Перезапустите контейнер
docker restart <postgrest-container-name>

# Или через docker-compose (если используется)
docker-compose restart postgrest
```

---

## 🔍 Шаг 5: Проверьте доступность функции через REST API

После перезапуска PostgREST попробуйте вызвать функцию через REST API:

### Через curl (если доступен):

```bash
curl -X POST "http://supabase.dev.neiromatrius.zerocoder.pro:8000/rest/v1/rpc/execute_sql" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjUyMDIwNTgsImV4cCI6MTg5MzQ1NjAwMCwicm9sZSI6ImFub24iLCJpc3MiOiJzdXBhYmFzZSJ9.aePmG2KknrQ8ofJdtvnQbhg0S8lEj8NLqsNsvOojucQ" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjUyMDIwNTgsImV4cCI6MTg5MzQ1NjAwMCwicm9sZSI6ImFub24iLCJpc3MiOiJzdXBhYmFzZSJ9.aePmG2KknrQ8ofJdtvnQbhg0S8lEj8NLqsNsvOojucQ" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT 1 as test", "read_only": true}'
```

**Ожидаемый результат:** `[{"test": 1}]` или похожий JSON массив

**Если ошибка 404 или "function not found":** PostgREST не видит функцию, нужно перезапустить.

---

## 🔄 Шаг 6: Перезапустите Cursor после перезапуска PostgREST

После перезапуска PostgREST контейнера:

1. **Полностью закройте Cursor**
2. **Запустите Cursor снова**
3. **Дождитесь инициализации MCP сервера** (обычно несколько секунд)
4. **Попробуйте выполнить MCP команды:**
   - `list_tables`
   - `execute_sql`

---

## 🔍 Шаг 7: Проверьте логи MCP сервера

Если MCP все еще не работает, проверьте логи:

1. **В Cursor:** Откройте Developer Tools (View → Developer → Toggle Developer Tools)
2. **Найдите логи MCP сервера** (обычно в консоли)
3. **Ищите сообщения:**
   - `"Checking for public.execute_sql RPC function..."`
   - `"'public.execute_sql' function found."` или `"'public.execute_sql' function not found"`
   - Ошибки подключения или выполнения

---

## 🎯 Альтернативное решение: Пересоздать функцию

Если ничего не помогает, пересоздайте функцию:

```sql
-- Удалить функцию (если существует)
DROP FUNCTION IF EXISTS public.execute_sql(text, boolean);

-- Создать функцию заново
CREATE OR REPLACE FUNCTION public.execute_sql(query text, read_only boolean DEFAULT false)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
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

-- Уведомить PostgREST о перезагрузке схемы
NOTIFY pgrst, 'reload schema';
```

**Изменения:**
- Добавлен `SECURITY DEFINER` для выполнения с правами создателя функции
- Добавлен `NOTIFY pgrst, 'reload schema'` в конце скрипта

После выполнения:
1. **Перезапустите PostgREST контейнер** (см. Шаг 4)
2. **Перезапустите Cursor** (см. Шаг 6)
3. **Проверьте работу MCP**

---

## 📋 Чеклист диагностики

- [ ] Функция существует в БД (Шаг 1)
- [ ] Права на функцию предоставлены (Шаг 2)
- [ ] Функция работает через SQL Editor (Шаг 3)
- [ ] PostgREST контейнер перезапущен (Шаг 4)
- [ ] Функция доступна через REST API (Шаг 5)
- [ ] Cursor перезапущен после перезапуска PostgREST (Шаг 6)
- [ ] Логи MCP сервера проверены (Шаг 7)
- [ ] Функция пересоздана с `SECURITY DEFINER` (если ничего не помогло)

---

## ⚠️ Важно

**PostgREST кэширует схему БД** и не знает о новых функциях до перезагрузки.

**`NOTIFY pgrst, 'reload schema'` может не сработать**, если:
- PostgREST не слушает уведомления
- PostgREST контейнер не перезапущен после создания функции
- Есть проблемы с подключением к БД

**Самое надежное решение:** Перезапустить PostgREST контейнер вручную.

---

**Дата:** 8 декабря 2025




