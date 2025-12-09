# 📋 Сводка сервисов Dokploy

**Дата:** 9 декабря 2025  
**Проект:** AI Customer Support System

---

## 🏗️ Архитектура сервисов

Проект состоит из **4 сервисов**, разворачиваемых в Dokploy:

### 1. 🔷 Supabase (Self-hosted)
- **Тип:** Отдельный сервис Dokploy (не в docker-compose проекта)
- **Назначение:** База данных PostgreSQL + REST API Gateway
- **Порт:** 8000 (Kong API Gateway), 5437 (PostgreSQL)
- **Миграции:** Выполняются вручную через SQL Editor
- **Файл миграций:** `database/migrations_supabase.sql`

**Настройки в .env:**
- `SUPABASE_URL` - URL API Gateway
- `SUPABASE_REST_URL` - REST API URL
- `SUPABASE_ANON_KEY` - Anon key
- `SUPABASE_SERVICE_KEY` - Service role key
- Или параметры прямого подключения: `SUPABASE_USER`, `SUPABASE_HOST`, `SUPABASE_PORT`, `SUPABASE_DB`

---

### 2. 🔴 Redis
- **Docker Compose:** `dokploy/docker-compose.redis.yml`
- **Образ:** `redis:7-alpine`
- **Контейнер:** `neiromatrius-redis`
- **Порт:** 6379
- **Команда запуска:** `redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru`
- **Healthcheck:** `redis-cli ping`

**Настройки в .env:**
- `REDIS_URL=redis://neiromatrius-redis:6379/0`

**Volumes:**
- `redis_data:/data`

---

### 3. ⚙️ Backend (FastAPI)
- **Docker Compose:** `dokploy/docker-compose.backend.yml`
- **Контейнер:** `neiromatrius-backend`
- **Порт:** 8000
- **Dockerfile:** `backend/Dockerfile`
- **Entrypoint:** `backend/scripts/entrypoint.sh`
- **Команда запуска:** `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4`
- **Healthcheck:** `curl -f http://localhost:8000/health`

**Основные переменные окружения:**
- `DATABASE_URL` или параметры Supabase
- `REDIS_URL`
- `OPENAI_API_KEY`
- `SECRET_KEY`
- `ALLOWED_ORIGINS`
- `TELEGRAM_BOT_TOKEN` (опционально)

**Зависимости:**
- Supabase (база данных)
- Redis (опционально, но рекомендуется)

---

### 4. 🎨 Frontend (Next.js)
- **Docker Compose:** `dokploy/docker-compose.frontend.yml`
- **Контейнер:** `neiromatrius-frontend`
- **Порт:** 3000
- **Dockerfile:** `frontend/Dockerfile`
- **Команда запуска:** `npm start` (production build)
- **Healthcheck:** `node -e "require('http').get('http://localhost:3000', ...)"`

**Основные переменные окружения:**
- `NODE_ENV=production`
- `NEXT_PUBLIC_API_URL=/api`
- `BACKEND_API_URL=http://neiromatrius-backend:8000`

**Зависимости:**
- Backend (для API запросов)

---

## 🌐 Docker Network

Все сервисы используют общую сеть:
- **Имя сети:** `neiromatrius-network`
- **Тип:** `external: true` (создается Dokploy автоматически)

**Взаимодействие между сервисами:**
- Frontend → Backend: `http://neiromatrius-backend:8000`
- Backend → Redis: `redis://neiromatrius-redis:6379/0`
- Backend → Supabase: через `SUPABASE_URL` или прямое подключение

---

## 📝 Порядок развертывания

1. **Supabase** - развернуть как отдельный сервис в Dokploy
2. **Redis** - развернуть через `docker-compose.redis.yml`
3. **Backend** - развернуть через `docker-compose.backend.yml`
4. **Frontend** - развернуть через `docker-compose.frontend.yml`

---

## ✅ Проверка соответствия

### Docker Compose файлы:
- ✅ `dokploy/docker-compose.backend.yml` - Backend сервис
- ✅ `dokploy/docker-compose.frontend.yml` - Frontend сервис
- ✅ `dokploy/docker-compose.redis.yml` - Redis сервис
- ✅ Supabase - отдельный сервис (не в docker-compose)

### Команды запуска:
- ✅ Redis: `redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru`
- ✅ Backend: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4` (через entrypoint.sh)
- ✅ Frontend: `npm start` (production build через Dockerfile)

### Переменные окружения:
- ✅ Все настройки описаны в `backend/.env.example`
- ✅ Разделены по секциям для каждого сервиса

