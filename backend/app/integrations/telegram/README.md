# Telegram Bot Integration

Модуль для интеграции Telegram бота с системой автоматизации клиентских сообщений.

## Назначение

Telegram бот используется для тестирования системы перед интеграцией с CRM заказчика и деплоем на production сервер.

## Функциональность

- ✅ Прием текстовых сообщений от пользователей
- ✅ Отправка сообщений в систему через `/api/messages/`
- ✅ Получение ответов от системы
- ✅ Отправка ответов обратно пользователям в Telegram
- ✅ Минимальный UX: команды `/start` и `/help`

## Настройка

### 1. Создание бота

1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен

### 2. Конфигурация

Добавьте в `backend/.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ENABLED=True
```

### 3. Запуск

#### Локальная разработка (Polling режим)

Бот автоматически запустится в polling режиме при старте приложения, если:
- `TELEGRAM_ENABLED=True`
- `TELEGRAM_BOT_TOKEN` установлен
- `TELEGRAM_WEBHOOK_URL` не установлен

#### Production (Webhook режим)

Для production используйте webhook:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ENABLED=True
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/integrations/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=your_secret_token_here
```

## Использование

1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Отправьте любое текстовое сообщение
4. Получите автоматический ответ от системы

## Архитектура

```
Telegram User → Telegram API → Bot Handler
                                      ↓
                            POST /api/messages/
                                      ↓
                            [Система обработки]
                                      ↓
                            Webhook → Telegram Response
                                      ↓
                            Telegram User
```

## Структура модуля

- `bot.py` - Основной класс бота
- `adapter.py` - Преобразование форматов (Telegram ↔ System)
- `sender.py` - Отправка ответов в Telegram
- `handlers.py` - Обработчики команд

## API Endpoints

- `POST /api/integrations/telegram/webhook` - Webhook для получения обновлений от Telegram
- `POST /api/integrations/telegram/response` - Внутренний endpoint для отправки ответов

## Безопасность

- Webhook валидация через секретный токен (опционально)
- Проверка типа чата (только приватные сообщения)
- Rate limiting через существующую систему

## Ограничения

- Только текстовые сообщения (можно расширить)
- Только приватные чаты (не группы)
- Минимальный UX (только базовые команды)










