# AI Customer Support System

Система первой линии поддержки на базе ИИ для автоматизации ответов клиентам.

## Технологии

- **Backend**: Python 3.10.19, FastAPI 0.104+
- **Frontend**: TypeScript, Next.js 14
- **Database**: PostgreSQL (Supabase)
- **AI**: OpenAI 4o mini (ProxyAPI для РФ)

## Структура проекта

```
ai-customer-support/
├── backend/          # FastAPI приложение
├── frontend/         # Next.js приложение
└── docker-compose.yml
```

## Быстрый старт

### Используя Docker Compose

1. Клонируйте репозиторий
2. Создайте `.env` файл в `backend/`:
   ```bash
   cp backend/.env.example backend/.env
   # Отредактируйте .env с вашими ключами
   ```
3. Запустите сервисы:
   ```bash
   docker-compose up
   ```
4. Откройте:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Ручная установка

См. `SETUP.md` для детальных инструкций.

## Разработка

Backend тесты:
```bash
cd backend
pytest tests/ -v
```

Frontend проверка типов:
```bash
cd frontend
npm run type-check
```

## Лицензия

MIT

