# 🐳 Docker Setup для PostgreSQL

## Статус

✅ PostgreSQL контейнер запущен и работает
✅ База данных `ai_support` создана
✅ Пользователь `support_user` настроен

## Команды для управления

### Запуск PostgreSQL
```bash
docker-compose up -d postgres
```

### Проверка статуса
```bash
docker-compose ps postgres
```

### Подключение к базе данных
```bash
docker-compose exec postgres psql -U support_user -d ai_support
```

### Остановка
```bash
docker-compose stop postgres
```

### Пересоздание (если нужно)
```bash
docker-compose down -v  # Удалит данные!
docker-compose up -d postgres
```

## Настройки подключения

- **Host**: localhost
- **Port**: 5432
- **Database**: ai_support
- **User**: support_user
- **Password**: support_pass

## URL для подключения

```
postgresql+asyncpg://support_user:support_pass@localhost:5432/ai_support
```

## Тестирование

Тесты автоматически используют PostgreSQL если он доступен, иначе используют SQLite (с ограничениями).

Для запуска тестов с PostgreSQL:
```bash
cd backend
python3 -m pytest tests/ -v
```

## Примечания

- PostgreSQL работает в Docker контейнере
- Данные сохраняются в Docker volume `postgres_data`
- Для production используйте более безопасные пароли

