# 🗄️ Руководство по подключению к Supabase через REST API

**Проект:** Neiromatrius  
**Дата:** 8 декабря 2025  
**Тип подключения:** Supabase REST API (требование заказчика)

---

## ⚠️ Важно

**По требованию заказчика система использует Supabase REST API, а не прямое PostgreSQL подключение.**

---

## 📋 Настройка подключения

### Шаг 1: Получение ключей из Supabase

1. Откройте **Supabase Dashboard**
2. Перейдите в **Settings** → **API**
3. Найдите следующие значения:

**Project URL:**
```
https://abcdefghijklmnop.supabase.co
```
→ Это ваш `SUPABASE_URL`

**service_role key:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
→ Это ваш `SUPABASE_SERVICE_KEY` (для полного доступа)

**anon key:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
→ Это ваш `SUPABASE_ANON_KEY` (если используется RLS)

### Шаг 2: Установка переменных окружения

В Dokploy для backend сервиса добавьте:

```bash
# Обязательно
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=your_service_key_here

# Или если используется RLS:
# SUPABASE_ANON_KEY=your_anon_key_here
```

⚠️ **Важно:** 
- `SUPABASE_SERVICE_KEY` дает полный доступ (обход RLS)
- `SUPABASE_ANON_KEY` требует настройки RLS политик
- Рекомендуется использовать `SUPABASE_SERVICE_KEY` для backend

---

## 🧪 Тестирование подключения

### Проверка REST API доступности

```bash
# Проверка базового доступа
curl -H "apikey: YOUR_SERVICE_KEY" \
     -H "Authorization: Bearer YOUR_SERVICE_KEY" \
     https://xxxxx.supabase.co/rest/v1/

# Проверка таблицы messages
curl -H "apikey: YOUR_SERVICE_KEY" \
     -H "Authorization: Bearer YOUR_SERVICE_KEY" \
     https://xxxxx.supabase.co/rest/v1/messages?limit=1
```

### Тест через Python скрипт

```python
# scripts/test_supabase_rest_api.py
import asyncio
from app.utils.supabase_adapter import get_supabase_adapter

async def test():
    adapter = await get_supabase_adapter()
    result = await adapter.select("messages", limit=1)
    print(f"✅ Подключение успешно: {len(result)} записей")
    await adapter.close()

asyncio.run(test())
```

---

## 🔧 Решение проблем

### Проблема: 401 Unauthorized

**Причина:** Неправильный ключ или отсутствие заголовков

**Решение:**
1. Проверьте правильность `SUPABASE_SERVICE_KEY`
2. Убедитесь, что ключ не истек
3. Проверьте заголовки в запросах

### Проблема: 404 Not Found

**Причина:** Неправильный URL или таблица не существует

**Решение:**
1. Проверьте `SUPABASE_URL` формат
2. Убедитесь, что миграции выполнены
3. Проверьте имя таблицы

### Проблема: 403 Forbidden

**Причина:** RLS политики блокируют доступ

**Решение:**
1. Используйте `SUPABASE_SERVICE_KEY` вместо `SUPABASE_ANON_KEY`
2. Или настройте RLS политики в Supabase

---

## 📊 Структура подключения

```
Backend (FastAPI)
    ↓
SupabaseAdapter (HTTP Client)
    ↓
Supabase REST API (PostgREST)
    ↓
PostgreSQL (Supabase self-hosted)
```

**Используется:**
- ✅ Supabase REST API через HTTP
- ✅ PostgREST для автоматической генерации API
- ✅ HTTP клиент (httpx) для запросов

**НЕ используется:**
- ❌ Прямое PostgreSQL подключение
- ❌ SQLAlchemy ORM (заменен на REST API)
- ❌ asyncpg драйвер

---

## 🔒 Безопасность

1. **Храните ключи в Secrets Dokploy**
   - Не храните в обычных переменных окружения
   - Используйте Secrets для чувствительных данных

2. **Используйте Service Key для backend**
   - Service Key дает полный доступ
   - Anon Key требует RLS политики

3. **Ограничьте доступ к Supabase**
   - Настройте firewall правила
   - Используйте VPN если возможно
   - Ограничьте доступ по IP адресу Dokploy сервера

---

## 📚 Дополнительная информация

- [Supabase REST API Docs](https://supabase.com/docs/reference/python/introduction)
- [PostgREST API Reference](https://postgrest.org/en/stable/api.html)
- [Supabase Python Client](https://github.com/supabase/supabase-py)

---

**Дата создания:** 8 декабря 2025







