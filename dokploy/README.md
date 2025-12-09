# 🚀 Dokploy Deployment

**Проект:** Neiromatrius  
**Платформа:** Dokploy

---

## 📁 Структура файлов

- `docker-compose.backend.yml` - Docker Compose конфигурация для backend сервиса
- `docker-compose.frontend.yml` - Docker Compose конфигурация для frontend сервиса
- `docker-compose.redis.yml` - Docker Compose конфигурация для Redis сервиса (опционально)
- `DOKPLOY_ENV_VARIABLES.md` - Документация по переменным окружения
- `DEPLOYMENT_GUIDE.md` - Подробное руководство по деплою
- `REDIS_SETUP.md` - Руководство по настройке Redis

---

## 🚀 Быстрый старт

1. **Подготовьте базу данных:**
   - Выполните миграции из `../database/migrations_supabase.sql` в Supabase SQL Editor

2. **Настройте сервисы в Dokploy (Docker Compose через Git):**
   - **Redis** (рекомендуется): `docker-compose.redis.yml` - см. `REDIS_QUICK_START.md`
   - **Backend**: `docker-compose.backend.yml`
   - **Frontend**: `docker-compose.frontend.yml`

3. **Настройте переменные окружения:**
   - См. `DOKPLOY_ENV_VARIABLES.md`

4. **Деплой:**
   - См. `DEPLOYMENT_GUIDE.md` для подробных инструкций

**Важно:** Все сервисы разворачиваются через Git репозиторий как Docker Compose сервисы, а не через встроенные templates Dokploy.

---

## 📚 Документация

- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Полное руководство по деплою
- [DOKPLOY_ENV_VARIABLES.md](./DOKPLOY_ENV_VARIABLES.md) - Переменные окружения

---

**Дата:** 8 декабря 2025

