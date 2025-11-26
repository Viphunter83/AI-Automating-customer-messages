# 🚀 Деплой на Vercel - Инструкция

**Дата:** 2025-11-27  
**Railway:** ✅ Успешно задеплоен

---

## 📋 Быстрый деплой

### Шаг 1: Инициализация проекта Vercel

```bash
vercel
```

**Ответьте на вопросы:**
- Set up and deploy? → `Y`
- Which scope? → `team_ckk1yHJodr9A9k87ScdWHwmQ` (Oleg's projects)
- Link to existing project? → `N`
- Project name? → `ai-customer-support-backend`
- Directory? → `.`
- Override settings? → `N`

### Шаг 2: Настройка переменных окружения

**ВАЖНО:** После инициализации настройте переменные в Vercel Dashboard:

1. Откройте [vercel.com/dashboard](https://vercel.com/dashboard)
2. Проект: `ai-customer-support-backend`
3. Settings → Environment Variables
4. Добавьте переменные:

**Обязательные:**
```
DATABASE_URL = [из Railway, формат: postgresql+asyncpg://...]
OPENAI_API_KEY = [ваш ключ от ProxyAPI]
SECRET_KEY = [случайная строка минимум 32 символа]
```

**Опциональные:**
```
OPENAI_API_BASE = https://api.proxyapi.ru/openai/v1
OPENAI_MODEL = gpt-4o-mini
DEBUG = False
LOG_LEVEL = INFO
```

**Важно:** Выберите окружения: ✅ Production, ✅ Preview, ✅ Development

### Шаг 3: Production деплой

```bash
vercel --prod
```

---

## ✅ Проверка

После деплоя проверьте:

```bash
# Health check
curl https://your-project.vercel.app/health

# API docs
open https://your-project.vercel.app/docs
```

---

## 📝 Получение DATABASE_URL из Railway

1. Откройте Railway Dashboard
2. PostgreSQL сервис → Variables
3. Скопируйте `DATABASE_URL` или `POSTGRES_URL`
4. **Измените формат:** `postgresql://` → `postgresql+asyncpg://`
5. Вставьте в Vercel как `DATABASE_URL`

---

**Готово!** После настройки переменных Vercel автоматически перезапустит деплой! 🚀

