# 🗄️ Создание базы данных через MCP Supabase

**Проект:** Neiromatrius  
**Дата:** 8 декабря 2025

---

## ✅ Готово к выполнению

SQL миграции готовы в файле `database/migrations_supabase.sql` (308 строк).

---

## 📋 Что будет создано

### ENUM типы (6):
- `messagetype` - типы сообщений
- `scenariotype` - сценарии классификации
- `remindertype` - типы напоминаний
- `dialogstatus` - статусы диалогов
- `prioritylevel` - уровни приоритета
- `escalationreason` - причины эскалации

### Таблицы (9):
1. `messages` - сообщения пользователей и ботов
2. `classifications` - классификация сообщений AI
3. `response_templates` - шаблоны ответов бота
4. `keywords` - ключевые слова для классификации
5. `operator_feedback` - обратная связь операторов
6. `operator_session_logs` - логи сессий операторов
7. `reminders` - напоминания для клиентов
8. `chat_sessions` - сессии чатов
9. `operator_message_reads` - отметки прочтения операторами

### Индексы (20+):
- Индексы для оптимизации запросов
- Составные индексы для сложных запросов
- Частичные индексы для уникальности

### Функции и триггеры:
- Функция `update_updated_at_column()` для автоматического обновления timestamp
- Триггеры для `chat_sessions` и `operator_message_reads`

---

## 🚀 Выполнение через MCP

**Попробуйте выполнить SQL через MCP Supabase в Cursor:**

1. Откройте файл `database/migrations_supabase.sql`
2. Скопируйте весь SQL код
3. Выполните через MCP Supabase

**Или выполните по секциям:**

### Секция 1: ENUM типы (строки 12-81)
### Секция 2: Таблицы (строки 84-193)
### Секция 3: Индексы (строки 196-238)
### Секция 4: Уникальные ограничения (строки 241-247)
### Секция 5: Функции и триггеры (строки 250-274)

---

## ✅ Проверка после выполнения

После выполнения миграций проверьте:

```sql
-- Проверка таблиц
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'messages', 'classifications', 'response_templates', 
    'keywords', 'operator_feedback', 'operator_session_logs',
    'reminders', 'chat_sessions', 'operator_message_reads'
)
ORDER BY table_name;

-- Проверка ENUM типов
SELECT typname 
FROM pg_type 
WHERE typtype = 'e' 
AND typname IN (
    'messagetype', 'scenariotype', 'remindertype', 
    'dialogstatus', 'prioritylevel', 'escalationreason'
)
ORDER BY typname;

-- Проверка индексов
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN (
    'messages', 'classifications', 'response_templates',
    'keywords', 'operator_feedback', 'reminders',
    'chat_sessions', 'operator_message_reads'
)
ORDER BY tablename, indexname;
```

---

**Дата:** 8 декабря 2025







