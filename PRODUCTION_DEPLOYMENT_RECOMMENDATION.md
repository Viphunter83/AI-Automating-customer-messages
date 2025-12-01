# 🚀 Рекомендации по Production деплою на сервер заказчика

## 📊 Анализ вариантов деплоя

### Вариант 1: Docker Compose + Nginx (✅ РЕКОМЕНДУЕТСЯ)

**Плюсы:**
- ✅ Простота настройки и поддержки
- ✅ Уже есть готовая конфигурация (`docker-compose.prod.yml`, `nginx.conf`)
- ✅ Легко масштабировать при необходимости
- ✅ Подходит для интеграции с CRM заказчика
- ✅ Полный контроль над инфраструктурой
- ✅ Легко делать бэкапы и миграции
- ✅ Поддержка WebSocket и background tasks (APScheduler)
- ✅ Низкие требования к знаниям DevOps

**Минусы:**
- ⚠️ Требует ручного управления обновлениями
- ⚠️ Нет автоматического масштабирования (но можно добавить позже)

**Подходит для:**
- Сервер заказчика с Docker
- Средняя/высокая нагрузка
- Требования к контролю и безопасности
- Интеграция с внутренней CRM

---

### Вариант 2: Kubernetes (❌ НЕ РЕКОМЕНДУЕТСЯ для начала)

**Плюсы:**
- ✅ Автоматическое масштабирование
- ✅ Высокая отказоустойчивость
- ✅ Продвинутое управление ресурсами

**Минусы:**
- ❌ Сложность настройки и поддержки
- ❌ Избыточно для текущего проекта
- ❌ Требует глубоких знаний Kubernetes
- ❌ Высокие требования к инфраструктуре

**Подходит для:**
- Очень высокая нагрузка
- Команда с опытом Kubernetes
- Требования к автоматическому масштабированию

---

### Вариант 3: Отдельные сервисы без Docker (❌ НЕ РЕКОМЕНДУЕТСЯ)

**Минусы:**
- ❌ Сложность настройки зависимостей
- ❌ Проблемы с версиями и совместимостью
- ❌ Сложнее обновления и миграции
- ❌ Нет изоляции окружений

---

## ✅ РЕКОМЕНДУЕМЫЙ ВАРИАНТ: Docker Compose + Nginx

### Архитектура деплоя:

```
┌─────────────────────────────────────────┐
│         Nginx (Reverse Proxy)           │
│         Port 80/443 (SSL)               │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌─────▼──────┐
│   Frontend  │  │   Backend   │
│  Next.js    │  │   FastAPI   │
│  Port 3000  │  │  Port 8000  │
└─────────────┘  └──────┬──────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼────┐  ┌──────▼──────┐  ┌────▼─────┐
│ PostgreSQL │  │    Redis    │  │ Telegram │
│  Port 5432 │  │  Port 6379  │  │   Bot    │
└────────────┘  └─────────────┘  └──────────┘
```

### Преимущества для заказчика:

1. **Простота управления:**
   ```bash
   # Запуск всей системы одной командой
   docker-compose -f docker-compose.prod.yml up -d
   
   # Остановка
   docker-compose -f docker-compose.prod.yml down
   
   # Обновление
   git pull && docker-compose -f docker-compose.prod.yml up -d --build
   ```

2. **Интеграция с CRM:**
   - Backend API доступен через Nginx
   - Легко настроить webhook для CRM
   - Поддержка всех необходимых endpoints

3. **Безопасность:**
   - Nginx как reverse proxy с SSL
   - Изоляция контейнеров
   - Легко настроить firewall

4. **Мониторинг и логи:**
   - Централизованные логи через Docker
   - Health checks для всех сервисов
   - Легко добавить Prometheus/Grafana

---

## 📋 План деплоя на сервер заказчика

### Шаг 1: Подготовка сервера

**Требования:**
- Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- Минимум 4GB RAM, 2 CPU cores
- 20GB свободного места
- Docker 20.10+ и Docker Compose 2.0+

**Установка Docker:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

### Шаг 2: Клонирование проекта

```bash
# На сервере заказчика
git clone <repository-url> ai-support
cd ai-support

# Создание production конфигурации
cp backend/.env.example backend/.env.production
cp docker-compose.prod.yml docker-compose.yml  # Для простоты
```

---

### Шаг 3: Настройка переменных окружения

**`backend/.env.production`:**
```env
# Database
DATABASE_URL=postgresql+asyncpg://support_user:STRONG_PASSWORD@postgres:5432/ai_support
DB_USER=support_user
DB_PASSWORD=STRONG_PASSWORD
DB_NAME=ai_support

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
OPENAI_MODEL=gpt-4o-mini

# Security
SECRET_KEY=GENERATE_STRONG_SECRET_KEY_MIN_32_CHARS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Redis (optional)
REDIS_URL=redis://redis:6379/0

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_ENABLED=true
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/api/integrations/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret

# Production settings
DEBUG=False
LOG_LEVEL=INFO
```

**`docker-compose.prod.yml` - обновить:**
```yaml
environment:
  NEXT_PUBLIC_API_URL: https://yourdomain.com/api
```

---

### Шаг 4: Настройка Nginx с SSL

**Установка Certbot (Let's Encrypt):**
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

**Настройка домена:**
```bash
# Получить SSL сертификат
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**Обновить `nginx.conf` для production:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket для операторов
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

### Шаг 5: Запуск production

```bash
# Сборка образов
docker-compose -f docker-compose.prod.yml build

# Запуск миграций
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Запуск всех сервисов
docker-compose -f docker-compose.prod.yml up -d

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps

# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f
```

---

### Шаг 6: Проверка работоспособности

```bash
# Health check
curl https://yourdomain.com/api/health

# Frontend
curl https://yourdomain.com

# Проверка всех сервисов
docker-compose -f docker-compose.prod.yml ps
```

---

## 🔄 Обновление системы

```bash
# 1. Остановка сервисов (опционально, можно без остановки)
docker-compose -f docker-compose.prod.yml stop backend frontend

# 2. Получение обновлений
git pull origin main

# 3. Пересборка и запуск
docker-compose -f docker-compose.prod.yml up -d --build

# 4. Применение миграций (если есть)
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# 5. Проверка
docker-compose -f docker-compose.prod.yml ps
curl https://yourdomain.com/api/health
```

---

## 📦 Бэкапы

### Автоматический бэкап БД:

**Создать скрипт `backup.sh`:**
```bash
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U support_user ai_support > $BACKUP_DIR/backup_$DATE.sql

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete
```

**Добавить в cron:**
```bash
# Ежедневный бэкап в 2:00
0 2 * * * /path/to/backup.sh
```

---

## 🔐 Безопасность

1. **Firewall:**
   ```bash
   sudo ufw allow 22/tcp    # SSH
   sudo ufw allow 80/tcp    # HTTP
   sudo ufw allow 443/tcp   # HTTPS
   sudo ufw enable
   ```

2. **Обновление Docker образов:**
   ```bash
   docker-compose -f docker-compose.prod.yml pull
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Мониторинг:**
   - Настроить логирование в централизованную систему
   - Настроить алерты на критические ошибки
   - Регулярно проверять обновления безопасности

---

## 📊 Мониторинг и метрики

**Доступные endpoints:**
- `https://yourdomain.com/api/health` - базовый health check
- `https://yourdomain.com/api/monitoring/metrics` - детальные метрики
- `https://yourdomain.com/api/monitoring/stats/summary` - сводка статистики

**Логи:**
```bash
# Все логи
docker-compose -f docker-compose.prod.yml logs -f

# Логи конкретного сервиса
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

---

## 🎯 Итоговые рекомендации

### ✅ Использовать Docker Compose + Nginx потому что:

1. **Простота:** Одна команда для запуска всей системы
2. **Готовность:** Уже есть вся необходимая конфигурация
3. **Гибкость:** Легко добавить новые сервисы или изменить конфигурацию
4. **Интеграция:** Идеально для интеграции с CRM заказчика
5. **Поддержка:** Легко передать поддержку заказчику
6. **Масштабирование:** При необходимости можно легко перейти на Kubernetes

### 📝 Следующие шаги:

1. ✅ Исправить frontend (сделано)
2. ✅ Подготовить production конфигурацию
3. 📋 Создать инструкцию для заказчика
4. 📋 Настроить автоматические бэкапы
5. 📋 Настроить мониторинг и алерты

---

## 📞 Поддержка

При возникновении проблем:
1. Проверить логи: `docker-compose logs`
2. Проверить health endpoints
3. Проверить статус контейнеров: `docker-compose ps`
4. Проверить ресурсы сервера: `docker stats`

