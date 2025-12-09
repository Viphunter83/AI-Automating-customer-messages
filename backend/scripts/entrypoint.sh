#!/bin/bash

set -e

echo "🚀 Starting Neiromatrius Backend..."

# Database migrations
# Note: For Supabase, migrations are executed manually via SQL Editor
# If using Alembic migrations, uncomment the following:
# echo "Running database migrations..."
# alembic upgrade head

# For Supabase: migrations are executed via database/migrations_supabase.sql
# This ensures schema is already created before backend starts
echo "✅ Database migrations should be executed via Supabase SQL Editor"

echo "Starting FastAPI server..."

exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4




