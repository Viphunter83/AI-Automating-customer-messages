# 🚀 Выполнение миграций в Self-Hosted Supabase

**Проект:** Neiromatrius  
**Self-Hosted Supabase:** supabase.dev.neiromatrius.zerocoder.pro  
**Дата:** 8 декабря 2025

---

## ✅ SQL миграции готовы

Файл: `database/migrations_supabase.sql` (308 строк)

---

## 📋 Способ 1: Через Supabase SQL Editor (рекомендуется)

### Шаг 1: Откройте Supabase Dashboard

1. Перейдите по адресу: `http://supabase.dev.neiromatrius.zerocoder.pro`
2. Войдите с учетными данными:
   - Username: `supabase` (из DASHBOARD_USERNAME)
   - Password: `ld1jah8qk5sigutjplm1n80dvn5jjjbz` (из DASHBOARD_PASSWORD)

### Шаг 2: Откройте SQL Editor

1. В левом меню выберите **SQL Editor**
2. Нажмите **New Query**

### Шаг 3: Выполните миграции

1. Откройте файл `database/migrations_supabase.sql`
2. Скопируйте весь SQL код (308 строк)
3. Вставьте в SQL Editor
4. Нажмите **Run** (или Ctrl+Enter)

---

## 📋 Способ 2: Через прямое подключение к PostgreSQL

### Подключение через psql

```bash
# Подключение к базе данных
psql -h supabase.dev.neiromatrius.zerocoder.pro \
     -p 5437 \
     -U postgres \
     -d postgres

# Пароль: tqwe8vpzjxptmged6w8v6cxm30fedpqg (из POSTGRES_PASSWORD)
```

### Выполнение миграций

```bash
# Выполнить SQL файл
psql -h supabase.dev.neiromatrius.zerocoder.pro \
     -p 5437 \
     -U postgres \
     -d postgres \
     -f database/migrations_supabase.sql
```

---

## 📋 Способ 3: Через Docker (если есть доступ к контейнеру)

```bash
# Выполнить SQL в контейнере PostgreSQL
docker exec -i neiromatrius-supabase-ckjmxl-supabase-db-1 \
  psql -U postgres -d postgres < database/migrations_supabase.sql
```

---

## ✅ Что будет создано

### ENUM типы (6):
- `messagetype`
- `scenariotype`
- `remindertype`
- `dialogstatus`
- `prioritylevel`
- `escalationreason`

### Таблицы (9):
- `messages`
- `classifications`
- `response_templates`
- `keywords`
- `operator_feedback`
- `operator_session_logs`
- `reminders`
- `chat_sessions`
- `operator_message_reads`

### Индексы (20+):
- Оптимизация запросов
- Составные индексы
- Частичные индексы

### Функции и триггеры:
- `update_updated_at_column()` функция
- Триггеры для автоматического обновления timestamp

---

## 🧪 Проверка после выполнения

После выполнения миграций выполните проверку в SQL Editor:

```sql
-- Проверка таблиц (должно быть 9)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'messages', 'classifications', 'response_templates', 
    'keywords', 'operator_feedback', 'operator_session_logs',
    'reminders', 'chat_sessions', 'operator_message_reads'
)
ORDER BY table_name;

-- Проверка ENUM типов (должно быть 6)
SELECT typname 
FROM pg_type 
WHERE typtype = 'e' 
AND typname IN (
    'messagetype', 'scenariotype', 'remindertype', 
    'dialogstatus', 'prioritylevel', 'escalationreason'
)
ORDER BY typname;
```

**Ожидаемый результат:**
- ✅ 9 таблиц созданы
- ✅ 6 ENUM типов созданы
- ✅ Все индексы созданы

---

## ⚠️ Важно

- SQL использует `IF NOT EXISTS` - безопасно выполнять повторно
- ENUM типы используют `DO $$ BEGIN ... EXCEPTION ... END $$` - безопасно
- Все операции идемпотентны - можно выполнять несколько раз

---

## 🔗 Полезные ссылки

- Supabase Dashboard: `http://supabase.dev.neiromatrius.zerocoder.pro`
- SQL Editor: `http://supabase.dev.neiromatrius.zerocoder.pro/project/default/sql`
- Database URL: `postgresql://postgres:tqwe8vpzjxptmged6w8v6cxm30fedpqg@supabase.dev.neiromatrius.zerocoder.pro:5437/postgres`

---

**Дата:** 8 декабря 2025







