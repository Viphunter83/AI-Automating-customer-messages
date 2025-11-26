# Setup & Development Guide

## Prerequisites

- Docker & Docker Compose
- Git
- Python 3.10+
- Node.js 18+

## Local Development Setup

### Using Docker Compose (Recommended)

1. Clone the repository:

   ```bash
   git clone <repo-url>
   cd ai-customer-support
   ```

2. Create `.env` file in root:

   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your OpenAI API key
   ```

3. Start services:

   ```bash
   docker-compose up
   ```

4. Access:

   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Manual Setup

#### Backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
# Run migrations (when ready)
# alembic upgrade head
uvicorn main:app --reload
```

#### Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Database Setup

### Для MVP: Локальная PostgreSQL (рекомендуется)

При использовании `docker-compose up` локальная БД создается автоматически. Никаких дополнительных действий не требуется.

Если запускаете без Docker, создайте локальную БД:

```bash
createuser support_user -P  # password: support_pass
createdb -O support_user ai_support
```

### Для Production: Supabase (опционально, на более поздних этапах)

1. Create account at https://supabase.com
2. Create new project
3. Copy connection string to backend/.env as DATABASE_URL
4. Раскомментируйте и заполните SUPABASE_URL и SUPABASE_ANON_KEY в .env
5. Run migrations

## Testing

Backend tests:

```bash
cd backend
pytest tests/ -v
```

## Project Structure

See ARCHITECTURE.md for detailed structure explanation.

