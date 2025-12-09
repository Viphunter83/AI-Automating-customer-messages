#!/usr/bin/env python3
"""
Скрипт для выполнения SQL миграций в self-hosted Supabase
Использует прямое подключение к PostgreSQL через psycopg2
"""

import sys
import os
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌ Ошибка: psycopg2 не установлен")
    print("Установите: pip install psycopg2-binary")
    sys.exit(1)

# Данные подключения из переменных окружения или напрямую
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "supabase.dev.neiromatrius.zerocoder.pro"),
    "port": int(os.getenv("POSTGRES_PORT", "5437")),
    "database": os.getenv("POSTGRES_DB", "postgres"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "tqwe8vpzjxptmged6w8v6cxm30fedpqg"),
}

MIGRATIONS_FILE = project_root / "database" / "migrations_supabase.sql"


def execute_migrations():
    """Выполняет SQL миграции из файла"""
    
    print("=" * 70)
    print("🚀 ВЫПОЛНЕНИЕ МИГРАЦИЙ В SELF-HOSTED SUPABASE")
    print("=" * 70)
    print()
    
    # Проверка файла миграций
    if not MIGRATIONS_FILE.exists():
        print(f"❌ Файл миграций не найден: {MIGRATIONS_FILE}")
        sys.exit(1)
    
    print(f"📁 Файл миграций: {MIGRATIONS_FILE}")
    
    # Чтение SQL файла
    with open(MIGRATIONS_FILE, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"📏 Размер SQL: {len(sql_content)} символов")
    print()
    
    # Подключение к базе данных
    print("🔌 Подключение к PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            connect_timeout=10
        )
        print("✅ Подключение успешно!")
        print()
        
        # Выполнение миграций
        print("📋 Выполнение миграций...")
        cur = conn.cursor()
        
        # Выполняем SQL по частям (разделяем по ;)
        # Но лучше выполнить весь блок целиком
        cur.execute(sql_content)
        
        conn.commit()
        print("✅ Миграции выполнены успешно!")
        print()
        
        # Проверка созданных таблиц
        print("🧪 Проверка созданных таблиц...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                'messages', 'classifications', 'response_templates', 
                'keywords', 'operator_feedback', 'operator_session_logs',
                'reminders', 'chat_sessions', 'operator_message_reads'
            )
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        print(f"✅ Создано таблиц: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Проверка ENUM типов
        cur.execute("""
            SELECT typname 
            FROM pg_type 
            WHERE typtype = 'e' 
            AND typname IN (
                'messagetype', 'scenariotype', 'remindertype', 
                'dialogstatus', 'prioritylevel', 'escalationreason'
            )
            ORDER BY typname;
        """)
        
        enums = cur.fetchall()
        print(f"✅ Создано ENUM типов: {len(enums)}")
        for enum in enums:
            print(f"   - {enum[0]}")
        
        cur.close()
        conn.close()
        
        print()
        print("=" * 70)
        print("✅ МИГРАЦИИ УСПЕШНО ВЫПОЛНЕНЫ!")
        print("=" * 70)
        
    except psycopg2.OperationalError as e:
        print(f"❌ Ошибка подключения: {e}")
        print()
        print("Возможные причины:")
        print("   1. PostgreSQL порт не открыт для внешних подключений")
        print("   2. Неправильные учетные данные")
        print("   3. Firewall блокирует подключение")
        print()
        print("Альтернативный способ:")
        print("   Выполните миграции через Supabase SQL Editor:")
        print("   http://supabase.dev.neiromatrius.zerocoder.pro")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка выполнения миграций: {e}")
        sys.exit(1)


if __name__ == "__main__":
    execute_migrations()







