# 🚀 Руководство по развертыванию системы на сервере заказчика

**Версия:** 1.0  
**Дата:** Декабрь 2025  
**Система:** AI Автоматизация клиентских сообщений

---

## 📋 Содержание

1. [Требования к серверу](#требования-к-серверу)
2. [Подготовка сервера](#подготовка-сервера)
3. [Установка системы](#установка-системы)
4. [Настройка переменных окружения](#настройка-переменных-окружения)
5. [Настройка SSL сертификата](#настройка-ssl-сертификата)
6. [Запуск системы](#запуск-системы)
7. [Проверка работоспособности](#проверка-работоспособности)
8. [Обновление системы](#обновление-системы)
9. [Резервное копирование](#резервное-копирование)
10. [Мониторинг и логи](#мониторинг-и-логи)
11. [Устранение неполадок](#устранение-неполадок)

---

## 📦 Требования к серверу

### Минимальные требования:
- **ОС:** Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / RHEL 8+
- **RAM:** 4 GB (рекомендуется 8 GB)
- **CPU:** 2 ядра (рекомендуется 4 ядра)
- **Диск:** 20 GB свободного места (рекомендуется 50 GB)
- **Сеть:** Статический IP адрес, доменное имя

### Программное обеспечение:
- Docker 20.10+ 
- Docker Compose 2.0+
- Git
- Nginx (опционально, если не используется контейнер)

---

## 🔧 Подготовка сервера

### Шаг 1: Обновление системы

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### Шаг 2: Установка Docker

```bash
# Универсальная установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавить текущего пользователя в группу docker
sudo usermod -aG docker $USER

# Выйти и войти снова для применения изменений
exit
```

### Шаг 3: Установка Docker Compose

```bash
# Установка последней версии Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker --version
docker-compose --version
```

### Шаг 4: Установка Git

```bash
# Ubuntu/Debian
sudo apt install git -y

# CentOS/RHEL
sudo yum install git -y
```

### Шаг 5: Настройка Firewall

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## 📥 Установка системы

### Шаг 1: Клонирование репозитория

```bash
# Создать директорию для проекта
sudo mkdir -p /opt/ai-support
sudo chown $USER:$USER /opt/ai-support
cd /opt/ai-support

# Клонировать репозиторий
git clone <URL_РЕПОЗИТОРИЯ> .

# Или если репозиторий приватный, используйте SSH:
# git clone git@github.com:your-org/ai-support.git .
```

### Шаг 2: Переход в директорию проекта

```bash
cd /opt/ai-support
```

---

## ⚙️ Настройка переменных окружения

### Шаг 1: Создание production конфигурации

```bash
# Скопировать пример конфигурации
cp backend/.env.production.example backend/.env.production

# Открыть файл для редактирования
nano backend/.env.production
```

### Шаг 2: Заполнение переменных окружения

Отредактируйте `backend/.env.production` и заполните следующие значения:

```env
# === DATABASE ===
DB_PASSWORD=ВАШ_СИЛЬНЫЙ_ПАРОЛЬ_БД  # Минимум 16 символов

# === OPENAI API ===
OPENAI_API_KEY=sk-ваш-ключ-openai

# === SECURITY ===
SECRET_KEY=ВАШ_СЕКРЕТНЫЙ_КЛЮЧ  # Генерируйте: openssl rand -hex 32
ALLOWED_ORIGINS=https://ваш-домен.com,https://www.ваш-домен.com

# === TELEGRAM BOT (опционально) ===
TELEGRAM_BOT_TOKEN=ваш-токен-бота
TELEGRAM_ENABLED=true
TELEGRAM_WEBHOOK_URL=https://ваш-домен.com/api/integrations/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=ваш-секрет-вебхука  # Генерируйте: openssl rand -hex 16
```

**Важно:**
- Используйте сильные пароли (минимум 16 символов)
- Генерируйте SECRET_KEY командой: `openssl rand -hex 32`
- Не коммитьте `.env.production` в git!

### Шаг 3: Настройка переменных для Docker Compose

Создайте файл `.env` в корне проекта (для docker-compose):

```bash
nano .env
```

Добавьте:

```env
# Database
DB_USER=support_user
DB_PASSWORD=ВАШ_ПАРОЛЬ_БД
DB_NAME=ai_support

# Frontend
NEXT_PUBLIC_API_URL=https://ваш-домен.com/api

# Backend (из backend/.env.production)
# Docker Compose автоматически загрузит backend/.env.production через env_file
```

---

## 🔒 Настройка SSL сертификата

### Вариант 1: Использование Nginx контейнера (рекомендуется)

Nginx контейнер уже настроен в `docker-compose.prod.yml`. Нужно только получить SSL сертификат.

### Вариант 2: Использование системного Nginx

Если вы используете системный Nginx (не контейнер):

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение SSL сертификата
sudo certbot --nginx -d ваш-домен.com -d www.ваш-домен.com

# Автоматическое обновление сертификата
sudo certbot renew --dry-run
```

### Вариант 3: Самоподписанный сертификат (только для тестирования)

```bash
# Создать директорию для SSL
mkdir -p ssl

# Генерировать самоподписанный сертификат
openssl req -x509 -newkey rsa:4096 -nodes \
  -out ssl/cert.pem -keyout ssl/key.pem -days 365 \
  -subj "/CN=ваш-домен.com"
```

**⚠️ Внимание:** Самоподписанные сертификаты не подходят для production!

---

## 🚀 Запуск системы

### Шаг 1: Сборка Docker образов

```bash
cd /opt/ai-support
docker-compose -f docker-compose.prod.yml build
```

Это может занять несколько минут при первом запуске.

### Шаг 2: Применение миграций базы данных

```bash
# Запустить миграции
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
```

### Шаг 3: Запуск всех сервисов

```bash
# Запуск в фоновом режиме
docker-compose -f docker-compose.prod.yml up -d

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps
```

Вы должны увидеть все сервисы в статусе "Up" или "healthy":
- `ai_support_db_prod` (PostgreSQL)
- `ai_support_redis_prod` (Redis)
- `ai_support_backend_prod` (Backend API)
- `ai_support_frontend_prod` (Frontend)
- `ai_support_nginx` (Nginx, если используется)

---

## ✅ Проверка работоспособности

### Шаг 1: Проверка health endpoints

```bash
# Health check backend
curl https://ваш-домен.com/api/health

# Детальные метрики
curl https://ваш-домен.com/api/monitoring/metrics
```

Ожидаемый ответ:
```json
{"status": "healthy", "timestamp": "...", "service": "ai-support-backend"}
```

### Шаг 2: Проверка frontend

Откройте в браузере:
```
https://ваш-домен.com
```

Должна открыться главная страница системы.

### Шаг 3: Проверка API документации

Откройте в браузере:
```
https://ваш-домен.com/api/docs
```

Должна открыться Swagger документация API.

### Шаг 4: Проверка статуса контейнеров

```bash
# Статус всех контейнеров
docker-compose -f docker-compose.prod.yml ps

# Логи всех сервисов
docker-compose -f docker-compose.prod.yml logs --tail=50
```

---

## 🔄 Обновление системы

### Процедура обновления:

```bash
cd /opt/ai-support

# 1. Остановить сервисы (опционально, можно без остановки)
docker-compose -f docker-compose.prod.yml stop backend frontend

# 2. Получить обновления из репозитория
git pull origin main

# 3. Пересобрать образы
docker-compose -f docker-compose.prod.yml build

# 4. Применить миграции БД (если есть новые)
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# 5. Запустить обновленные сервисы
docker-compose -f docker-compose.prod.yml up -d

# 6. Проверить статус
docker-compose -f docker-compose.prod.yml ps
curl https://ваш-домен.com/api/health
```

### Автоматическое обновление (опционально)

Создайте скрипт `/opt/ai-support/update.sh`:

```bash
#!/bin/bash
cd /opt/ai-support
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
docker-compose -f docker-compose.prod.yml up -d
echo "Обновление завершено!"
```

Сделайте его исполняемым:
```bash
chmod +x /opt/ai-support/update.sh
```

---

## 💾 Резервное копирование

### Автоматический бэкап базы данных

Создайте скрипт `/opt/ai-support/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/ai-support"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Бэкап базы данных
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U support_user ai_support > $BACKUP_DIR/db_backup_$DATE.sql

# Сжатие бэкапа
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Бэкап создан: $BACKUP_DIR/db_backup_$DATE.sql.gz"
```

Сделайте его исполняемым:
```bash
chmod +x /opt/ai-support/backup.sh
```

### Настройка автоматического бэкапа (cron)

```bash
# Открыть crontab
crontab -e

# Добавить строку для ежедневного бэкапа в 2:00
0 2 * * * /opt/ai-support/backup.sh >> /var/log/ai-support-backup.log 2>&1
```

### Восстановление из бэкапа

```bash
# Остановить сервисы
docker-compose -f docker-compose.prod.yml stop backend

# Распаковать бэкап
gunzip /opt/backups/ai-support/db_backup_YYYYMMDD_HHMMSS.sql.gz

# Восстановить
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U support_user ai_support < /opt/backups/ai-support/db_backup_YYYYMMDD_HHMMSS.sql

# Запустить сервисы
docker-compose -f docker-compose.prod.yml start backend
```

---

## 📊 Мониторинг и логи

### Просмотр логов

```bash
# Все логи
docker-compose -f docker-compose.prod.yml logs -f

# Логи конкретного сервиса
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f postgres

# Последние 100 строк
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Использование диска
docker system df
```

### Метрики системы

Доступны через API:
- `https://ваш-домен.com/api/monitoring/metrics` - детальные метрики
- `https://ваш-домен.com/api/monitoring/stats/summary` - сводка статистики

---

## 🔧 Устранение неполадок

### Проблема: Контейнеры не запускаются

```bash
# Проверить логи
docker-compose -f docker-compose.prod.yml logs

# Проверить статус
docker-compose -f docker-compose.prod.yml ps

# Пересоздать контейнеры
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

### Проблема: Ошибка подключения к базе данных

```bash
# Проверить статус PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U support_user

# Проверить логи PostgreSQL
docker-compose -f docker-compose.prod.yml logs postgres
```

### Проблема: Frontend не открывается

```bash
# Проверить логи frontend
docker-compose -f docker-compose.prod.yml logs frontend

# Проверить доступность backend API
curl https://ваш-домен.com/api/health

# Перезапустить frontend
docker-compose -f docker-compose.prod.yml restart frontend
```

### Проблема: SSL сертификат не работает

```bash
# Проверить конфигурацию Nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Перезапустить Nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Проблема: Недостаточно места на диске

```bash
# Очистить неиспользуемые Docker ресурсы
docker system prune -a --volumes

# Проверить использование диска
df -h
docker system df
```

---

## 📞 Поддержка

### Полезные команды

```bash
# Перезапуск всех сервисов
docker-compose -f docker-compose.prod.yml restart

# Остановка всех сервисов
docker-compose -f docker-compose.prod.yml stop

# Запуск всех сервисов
docker-compose -f docker-compose.prod.yml start

# Удаление всех контейнеров и volumes (ОСТОРОЖНО!)
docker-compose -f docker-compose.prod.yml down -v
```

### Контакты для поддержки

При возникновении проблем:
1. Проверьте логи: `docker-compose logs`
2. Проверьте health endpoints
3. Проверьте статус контейнеров: `docker-compose ps`
4. Обратитесь к разработчикам с логами ошибок

---

## ✅ Чеклист после установки

- [ ] Все контейнеры запущены и работают
- [ ] Health check возвращает "healthy"
- [ ] Frontend открывается в браузере
- [ ] API документация доступна
- [ ] SSL сертификат настроен и работает
- [ ] Автоматический бэкап настроен
- [ ] Firewall настроен правильно
- [ ] Переменные окружения заполнены
- [ ] Миграции БД применены
- [ ] Мониторинг работает

---

**Успешного развертывания! 🚀**

