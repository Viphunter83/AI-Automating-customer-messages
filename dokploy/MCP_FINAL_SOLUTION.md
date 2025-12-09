# ✅ Финальное решение проблемы MCP

**Проблема:** MCP сервер не видит функцию `execute_sql` даже после перезапуска PostgREST и Cursor.

**Дата:** 8 декабря 2025

---

## 🔍 Диагностика

Если MCP все еще не работает после:
- ✅ Создания функции `execute_sql`
- ✅ Предоставления прав
- ✅ Выполнения `NOTIFY pgrst, 'reload schema'`
- ✅ Перезапуска PostgREST контейнера
- ✅ Перезапуска Cursor

То проблема может быть в:
1. **Функция не имеет `SECURITY DEFINER`** - нужна для выполнения с правами создателя
2. **Функция не имеет `SET search_path`** - может быть проблема с поиском схемы
3. **PostgREST не видит функцию** - нужно пересоздать с правильными параметрами

---

## ✅ Решение: Пересоздать функцию

### Шаг 1: Выполните SQL в Supabase SQL Editor

Откройте файл `dokploy/MCP_FUNCTION_RECREATE.sql` и выполните весь SQL код в Supabase SQL Editor.

**Или скопируйте и выполните:**

```sql
-- Удалить функцию (если существует)
DROP FUNCTION IF EXISTS public.execute_sql(text, boolean);

-- Создать функцию заново с SECURITY DEFINER
CREATE OR REPLACE FUNCTION public.execute_sql(query text, read_only boolean DEFAULT false)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
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
    RAISE EXCEPTION 'Error executing SQL (SQLSTATE: %): % ', SQLERRM;
END;
$$;

-- Предоставить права на выполнение функции
GRANT EXECUTE ON FUNCTION public.execute_sql(text, boolean) TO authenticated;
GRANT EXECUTE ON FUNCTION public.execute_sql(text, boolean) TO anon;
GRANT EXECUTE ON FUNCTION public.execute_sql(text, boolean) TO service_role;

-- Уведомить PostgREST о перезагрузке схемы
NOTIFY pgrst, 'reload schema';
```

### Шаг 2: Перезапустите PostgREST контейнер

После выполнения SQL:

1. **Откройте Dokploy Dashboard**
2. **Найдите сервис Supabase**
3. **Найдите контейнер `postgrest`**
4. **Перезапустите контейнер**

### Шаг 3: Перезапустите Cursor

После перезапуска PostgREST:

1. **Полностью закройте Cursor**
2. **Запустите Cursor снова**
3. **Дождитесь инициализации MCP сервера**

### Шаг 4: Проверьте работу MCP

После перезапуска Cursor попробуйте:

```bash
# В Cursor через MCP инструменты
list_tables
execute_sql: SELECT 1 as test;
```

---

## 🔍 Если все еще не работает

### Альтернатива 1: Проверьте функцию через REST API напрямую

Если у вас есть доступ к Supabase через браузер, попробуйте вызвать функцию через REST API:

```javascript
// В браузере (консоль разработчика) или через curl
fetch('http://supabase.dev.neiromatrius.zerocoder.pro:8000/rest/v1/rpc/execute_sql', {
  method: 'POST',
  headers: {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjUyMDIwNTgsImV4cCI6MTg5MzQ1NjAwMCwicm9sZSI6ImFub24iLCJpc3MiOiJzdXBhYmFzZSJ9.aePmG2KknrQ8ofJdtvnQbhg0S8lEj8NLqsNsvOojucQ',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjUyMDIwNTgsImV4cCI6MTg5MzQ1NjAwMCwicm9sZSI6ImFub24iLCJpc3MiOiJzdXBhYmFzZSJ9.aePmG2KknrQ8ofJdtvnQbhg0S8lEj8NLqsNsvOojucQ',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'SELECT 1 as test',
    read_only: true
  })
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

**Ожидаемый результат:** `[{"test": 1}]`

**Если ошибка 404:** PostgREST не видит функцию, нужно перезапустить PostgREST.

**Если ошибка 500:** Проблема с функцией, проверьте логи.

### Альтернатива 2: Используйте Supabase SQL Editor для миграций

Если MCP все еще не работает, используйте **Supabase SQL Editor** для выполнения миграций:

1. **Откройте Supabase SQL Editor**
2. **Скопируйте весь файл `database/migrations_supabase.sql`**
3. **Выполните SQL код**
4. **Проверьте результат**

**Преимущества:**
- ✅ Работает всегда (не зависит от MCP)
- ✅ Выполнение всего скрипта за раз
- ✅ Транзакции работают корректно
- ✅ Легче отслеживать ошибки

---

## 📋 Чеклист

- [ ] Функция пересоздана с `SECURITY DEFINER` и `SET search_path`
- [ ] Права на функцию предоставлены (`authenticated`, `anon`, `service_role`)
- [ ] Выполнена команда `NOTIFY pgrst, 'reload schema'`
- [ ] PostgREST контейнер перезапущен
- [ ] Cursor перезапущен
- [ ] MCP команда `list_tables` работает
- [ ] MCP команда `execute_sql` работает
- [ ] Или миграции выполнены через SQL Editor

---

## 🎯 Рекомендация

**Для миграций:** Используйте **Supabase SQL Editor** - это самый надежный способ, не зависит от MCP.

**Для работы с данными:** После успешной настройки MCP используйте его для запросов и операций с данными.

---

**Дата:** 8 декабря 2025



