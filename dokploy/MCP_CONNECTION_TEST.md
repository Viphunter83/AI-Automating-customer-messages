# 🧪 Тест подключения к Supabase через MCP

**Проект:** Neiromatrius  
**Дата:** 8 декабря 2025

---

## ✅ Результат проверки

**MCP Supabase доступен в Cursor!**

---

## 📋 Структура базы данных

Из миграций (`database/migrations_supabase.sql`) и моделей (`backend/app/models/database.py`) видно:

### Таблицы:

1. **messages** - Сообщения пользователей и ботов
   - id (UUID)
   - client_id (VARCHAR)
   - content (TEXT)
   - message_type (messagetype ENUM)
   - is_processed (BOOLEAN)
   - is_first_message (BOOLEAN)
   - priority (prioritylevel ENUM)
   - escalation_reason (escalationreason ENUM)
   - created_at (TIMESTAMP)

2. **classifications** - Классификация сообщений AI
   - id (UUID)
   - message_id (UUID, FK → messages)
   - detected_scenario (scenariotype ENUM)
   - confidence (FLOAT)
   - ai_model (VARCHAR)
   - reasoning (TEXT)
   - created_at (TIMESTAMP)

3. **response_templates** - Шаблоны ответов бота
   - id (UUID)
   - scenario_name (VARCHAR)
   - template_text (TEXT)
   - is_active (BOOLEAN)
   - created_at, updated_at (TIMESTAMP)

4. **keywords** - Ключевые слова для классификации
   - id (UUID)
   - keyword (VARCHAR)
   - scenario (scenariotype ENUM)
   - weight (FLOAT)
   - is_active (BOOLEAN)

5. **operator_feedback** - Обратная связь операторов
   - id (UUID)
   - message_id (UUID, FK → messages)
   - operator_id (VARCHAR)
   - feedback_type (VARCHAR)
   - comment (TEXT)
   - created_at (TIMESTAMP)

6. **operator_session_logs** - Логи сессий операторов
   - id (UUID)
   - operator_id (VARCHAR)
   - session_start (TIMESTAMP)
   - session_end (TIMESTAMP)
   - messages_handled (INTEGER)

7. **reminders** - Напоминания для клиентов
   - id (UUID)
   - client_id (VARCHAR)
   - message_id (UUID, FK → messages)
   - reminder_type (remindertype ENUM)
   - scheduled_at (TIMESTAMP)
   - sent_at (TIMESTAMP)
   - is_cancelled (BOOLEAN)

8. **chat_sessions** - Сессии чатов
   - id (UUID)
   - client_id (VARCHAR, UNIQUE)
   - status (dialogstatus ENUM)
   - last_activity_at (TIMESTAMP)
   - closed_at (TIMESTAMP)
   - farewell_sent_at (TIMESTAMP)
   - webhook_url (VARCHAR)
   - platform (VARCHAR)
   - chat_id (VARCHAR)

9. **operator_message_reads** - Отметки прочтения операторами
   - id (UUID)
   - message_id (UUID, FK → messages)
   - operator_id (VARCHAR)
   - read_at (TIMESTAMP)

### ENUM типы:

- **messagetype**: 'user', 'bot_auto', 'bot_escalated', 'operator'
- **scenariotype**: 'GREETING', 'REFERRAL', 'TECH_SUPPORT_BASIC', 'FAREWELL', 'REMINDER', 'ABSENCE_REQUEST', 'SCHEDULE_CHANGE', 'COMPLAINT', 'MISSING_TRAINER', 'MASS_OUTAGE', 'REVIEW_BONUS', 'CROSS_EXTENSION', 'LESSON_CANCELLATION', 'LESSON_LINK', 'GREETING_TIME_REQUEST', 'UNKNOWN', 'ESCALATED'
- **remindertype**: 'reminder_15min', 'reminder_30min', 'reminder_1day'
- **dialogstatus**: 'open', 'closed', 'escalated'
- **prioritylevel**: 'low', 'medium', 'high', 'critical'
- **escalationreason**: 'low_confidence', 'repeated_failed', 'complaint', 'unknown_scenario', 'operator_marked', 'system_error'

---

## 🔍 Примеры запросов через MCP

### 1. Проверка таблиц

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

### 2. Количество сообщений

```sql
SELECT COUNT(*) as total_messages FROM messages;
```

### 3. Последние сообщения

```sql
SELECT id, client_id, content, message_type, created_at 
FROM messages 
ORDER BY created_at DESC 
LIMIT 10;
```

### 4. Статистика по сценариям

```sql
SELECT 
    detected_scenario,
    COUNT(*) as count,
    AVG(confidence) as avg_confidence
FROM classifications
GROUP BY detected_scenario
ORDER BY count DESC;
```

### 5. Активные диалоги

```sql
SELECT 
    client_id,
    status,
    last_activity_at,
    platform
FROM chat_sessions
WHERE status = 'open'
ORDER BY last_activity_at DESC;
```

---

## ✅ Статус подключения

**MCP Supabase доступен в Cursor!**

Можно использовать для:
- ✅ Выполнения SQL запросов
- ✅ Просмотра структуры БД
- ✅ Управления данными
- ✅ Проверки миграций

---

**Дата:** 8 декабря 2025







