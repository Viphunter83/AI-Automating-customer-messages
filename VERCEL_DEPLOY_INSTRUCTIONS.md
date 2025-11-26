# 🚀 Инструкция по деплою на Vercel

**Дата:** 2025-11-27  
**Railway:** ✅ Успешно задеплоен

---

## 📋 Пошаговая инструкция

### Шаг 1: Авторизация в Vercel

```bash
vercel login
```

Следуйте инструкциям в браузере для авторизации.

---

### Шаг 2: Инициализация проекта

```bash
vercel
```

**Ответьте на вопросы:**
- Set up and deploy? → `Y`
- Which scope? → Выберите `team_ckk1yHJodr9A9k87ScdWHwmQ` (Oleg's projects)
- Link to existing project? → `N` (создать новый)
- Project name? → `ai-customer-support-backend` (или любое имя)
- Directory? → `.` (текущая директория)
- Override settings? → `N`

После этого создастся папка `.vercel` с конфигурацией проекта.

---

### Шаг 3: Получите DATABASE_URL из Railway

1. Откройте [railway.app](https://railway.app)
2. PostgreSQL сервис → Variables
3. Скопируйте `DATABASE_URL` или `POSTGRES_URL`
4. **Измените формат:** `postgresql://` → `postgresql+asyncpg://`

**Пример:**
```
Было:  postgresql://postgres:password@host:5432/railway
Нужно: postgresql+asyncpg://postgres:password@host:5432/railway
```

---

### Шаг 4: Настройка переменных окружения в Vercel

**Через Dashboard (рекомендуется):**

1. Откройте [vercel.com/dashboard](https://vercel.com/dashboard)
2. Найдите проект `ai-customer-support-backend`
3. Settings → Environment Variables
4. Добавьте переменные:

**Обязательные:**
```
DATABASE_URL = postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway
OPENAI_API_KEY = sk-your-api-key-here
SECRET_KEY = your-secret-key-minimum-32-characters-long
```

**Опциональные:**
```
OPENAI_API_BASE = https://api.proxyapi.ru/openai/v1
OPENAI_MODEL = gpt-4o-mini
DEBUG = False
LOG_LEVEL = INFO
```

**Важно:**
- ✅ Выберите окружения: **Production**, **Preview**, **Development**
- ✅ Сохраните каждую переменную

**Через CLI (альтернатива):**

```bash
vercel env add DATABASE_URL production
# Вставьте значение DATABASE_URL из Railway

vercel env add OPENAI_API_KEY production
# Вставьте ваш API ключ

vercel env add SECRET_KEY production
# Вставьте случайную строку минимум 32 символа
```

---

### Шаг 5: Production деплой

```bash
vercel --prod
```

После деплоя вы получите URL вида: `https://your-project.vercel.app`

---

## ✅ Проверка после деплоя

```bash
# Health check
curl https://your-project.vercel.app/health

# API docs
open https://your-project.vercel.app/docs

# Тест API
curl -X POST https://your-project.vercel.app/api/messages/ \
  -H "Content-Type: application/json" \
  -d '{"client_id": "test", "content": "Привет"}'
```

---

## 🔧 Если что-то пошло не так

### Проблема: Переменные окружения не применяются

**Решение:**
1. Проверьте, что переменные добавлены в правильный проект
2. Убедитесь, что выбраны все окружения (Production, Preview, Development)
3. Перезапустите деплой: `vercel --prod`

### Проблема: Ошибка подключения к БД

**Решение:**
1. Проверьте формат `DATABASE_URL`: должен быть `postgresql+asyncpg://`
2. Убедитесь, что Railway PostgreSQL доступен извне
3. Проверьте логи в Vercel Dashboard → Deployments → Logs

### Проблема: Ошибка импорта модулей

**Решение:**
1. Убедитесь, что `requirements.txt` содержит все зависимости
2. Проверьте, что `api/index.py` правильно настроен
3. Проверьте логи сборки в Vercel Dashboard

---

## 📊 Архитектура после деплоя

```
┌─────────────┐
│   Vercel    │  ← FastAPI Backend (Serverless)
│  (Backend)  │     https://your-project.vercel.app
└──────┬──────┘
       │
       │ DATABASE_URL
       │
┌──────▼──────┐
│   Railway    │  ← PostgreSQL Database
│   (PostgreSQL)│   postgresql+asyncpg://...
└─────────────┘
```

---

## 🎯 Готово!

После выполнения всех шагов ваш FastAPI бэкенд будет задеплоен на Vercel и подключен к PostgreSQL на Railway!

**Следующие шаги:**
1. ✅ Выполните `vercel login`
2. ✅ Выполните `vercel` для инициализации
3. ✅ Настройте переменные окружения в Dashboard
4. ✅ Выполните `vercel --prod` для production деплоя

---

**Удачи с деплоем!** 🚀

