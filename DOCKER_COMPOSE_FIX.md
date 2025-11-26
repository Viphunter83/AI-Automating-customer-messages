# 🔧 Исправление предупреждений docker-compose

**Дата:** 2025-11-26  
**Проблема:** Предупреждения о не установленных переменных окружения

---

## 🐛 Проблема

Docker-compose показывал предупреждения:
```
WARN[0000] The "DEBUG" variable is not set. Defaulting to a blank string.
WARN[0000] The "LOG_LEVEL" variable is not set. Defaulting to a blank string.
WARN[0000] The "SECRET_KEY" variable is not set. Defaulting to a blank string.
...
```

**Причина:**
- В `docker-compose.yml` переменные были указаны в секции `environment` с синтаксисом `${VARIABLE}`
- Docker-compose пытался разрешить эти переменные из окружения хоста ДО загрузки `env_file`
- Если переменные не были установлены в окружении хоста, появлялись предупреждения

---

## ✅ Решение

Убрано дублирование переменных из секции `environment`:

**До:**
```yaml
env_file:
  - ./backend/.env
environment:
  DATABASE_URL: postgresql+asyncpg://support_user:support_pass@postgres:5432/ai_support
  SUPABASE_URL: ${SUPABASE_URL}
  SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
  OPENAI_API_KEY: ${OPENAI_API_KEY}
  # ... и т.д.
```

**После:**
```yaml
env_file:
  - ./backend/.env
environment:
  # Override DATABASE_URL for Docker network (use postgres service name instead of localhost)
  DATABASE_URL: postgresql+asyncpg://support_user:support_pass@postgres:5432/ai_support
  # All other variables are loaded from backend/.env automatically
```

---

## 📝 Объяснение

1. **env_file** автоматически загружает все переменные из `backend/.env`
2. **environment** используется только для переопределения `DATABASE_URL` (нужно использовать имя сервиса `postgres` вместо `localhost`)
3. Все остальные переменные загружаются из `.env` файла без предупреждений

---

## ✅ Результат

- ✅ Предупреждения исчезли
- ✅ Все переменные загружаются корректно из `backend/.env`
- ✅ Приложение работает как и прежде
- ✅ Код стал чище и проще

---

**Статус:** ✅ Исправлено

