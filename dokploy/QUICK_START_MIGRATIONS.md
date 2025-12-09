# ⚡ Быстрый старт: Выполнение миграций

**Проект:** Neiromatrius  
**Self-Hosted Supabase:** supabase.dev.neiromatrius.zerocoder.pro

---

## 🚀 Самый простой способ (через SQL Editor)

### 1. Откройте Supabase Dashboard

Перейдите по адресу: **http://supabase.dev.neiromatrius.zerocoder.pro**

### 2. Войдите в систему

- **Username:** `supabase`
- **Password:** `ld1jah8qk5sigutjplm1n80dvn5jjjbz`

### 3. Откройте SQL Editor

1. В левом меню нажмите **SQL Editor**
2. Нажмите **New Query**

### 4. Выполните миграции

1. Откройте файл `database/migrations_supabase.sql` в вашем редакторе
2. Скопируйте **весь SQL код** (Ctrl+A, затем Ctrl+C)
3. Вставьте в SQL Editor (Ctrl+V)
4. Нажмите **Run** (или Ctrl+Enter)

### 5. Проверьте результат

После выполнения вы должны увидеть сообщение об успешном выполнении.

---

## ✅ Что будет создано

- ✅ 6 ENUM типов
- ✅ 9 таблиц
- ✅ 20+ индексов
- ✅ Функции и триггеры

---

## 🧪 Проверка после выполнения

Выполните этот запрос в SQL Editor:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'messages', 'classifications', 'response_templates', 
    'keywords', 'operator_feedback', 'operator_session_logs',
    'reminders', 'chat_sessions', 'operator_message_reads'
)
ORDER BY table_name;
```

Должно вернуться **9 таблиц**.

---

**Готово!** База данных создана и готова к использованию.







