#!/usr/bin/env python3
"""
Валидация конфигурации перед деплоем
"""
import os
import sys
import json
from pathlib import Path

def check_env_file():
    """Проверка наличия .env файлов"""
    print("=" * 70)
    print("🔍 ПРОВЕРКА КОНФИГУРАЦИОННЫХ ФАЙЛОВ")
    print("=" * 70)
    print()
    
    errors = []
    warnings = []
    
    # Backend .env
    backend_env = Path("backend/.env")
    backend_example = Path("backend/.env.example")
    
    if not backend_env.exists():
        warnings.append(f"⚠️  backend/.env не найден (используйте backend/.env.example как шаблон)")
    else:
        print("✅ backend/.env найден")
    
    # Frontend .env
    frontend_env = Path("frontend/.env.local")
    if not frontend_env.exists():
        print("ℹ️  frontend/.env.local не найден (не критично для production)")
    
    return errors, warnings

def validate_docker_compose():
    """Проверка Docker Compose файлов"""
    print()
    print("=" * 70)
    print("🔍 ПРОВЕРКА DOCKER COMPOSE ФАЙЛОВ")
    print("=" * 70)
    print()
    
    files_to_check = [
        "dokploy/docker-compose.backend.yml",
        "dokploy/docker-compose.frontend.yml",
        "dokploy/docker-compose.redis.yml",
    ]
    
    errors = []
    
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path} найден")
            
            # Проверка содержимого
            content = path.read_text()
            
            # Проверка на использование переменных окружения (только для backend/frontend)
            if "redis" not in file_path:
                if "${" not in content and "$" not in content:
                    errors.append(f"⚠️  {file_path}: не найдены переменные окружения (${{VAR}})")
            
            # Проверка на healthcheck
            if "healthcheck" not in content.lower():
                errors.append(f"⚠️  {file_path}: отсутствует healthcheck")
        else:
            if "redis" in file_path:
                print(f"ℹ️  {file_path} не найден (Redis опционален)")
            else:
                errors.append(f"❌ {file_path} не найден")
    
    return errors

def validate_sql_migrations():
    """Проверка SQL миграций"""
    print()
    print("=" * 70)
    print("🔍 ПРОВЕРКА SQL МИГРАЦИЙ")
    print("=" * 70)
    print()
    
    sql_file = Path("database/migrations_supabase.sql")
    
    if not sql_file.exists():
        print("❌ database/migrations_supabase.sql не найден")
        return False
    
    print("✅ database/migrations_supabase.sql найден")
    
    content = sql_file.read_text()
    
    # Проверка основных элементов
    checks = {
        "CREATE TYPE": "ENUM типы",
        "CREATE TABLE": "Таблицы",
        "CREATE INDEX": "Индексы",
        "CREATE FUNCTION": "Функции",
        "CREATE TRIGGER": "Триггеры",
    }
    
    for keyword, description in checks.items():
        if keyword in content:
            print(f"✅ {description} найдены")
        else:
            print(f"⚠️  {description} не найдены")
    
    return True

def main():
    """Главная функция"""
    print()
    
    # Проверка файлов
    env_errors, env_warnings = check_env_file()
    
    # Проверка Docker Compose
    compose_errors = validate_docker_compose()
    
    # Проверка миграций
    migrations_ok = validate_sql_migrations()
    
    # Итоги
    print()
    print("=" * 70)
    print("📊 ИТОГИ ПРОВЕРКИ")
    print("=" * 70)
    print()
    
    all_errors = env_errors + compose_errors
    
    if all_errors:
        print("❌ НАЙДЕНЫ ОШИБКИ:")
        for error in all_errors:
            print(f"   {error}")
        print()
    
    if env_warnings:
        print("⚠️  ПРЕДУПРЕЖДЕНИЯ:")
        for warning in env_warnings:
            print(f"   {warning}")
        print()
    
    if not all_errors and migrations_ok:
        print("✅ Все проверки пройдены!")
        print("   Проект готов к деплою")
        return 0
    else:
        print("❌ Исправьте ошибки перед деплоем")
        return 1

if __name__ == "__main__":
    sys.exit(main())

