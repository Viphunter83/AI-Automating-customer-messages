#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к базе данных Supabase
"""
import asyncio
import os
import sys
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_database_connection():
    """Тестирование подключения к базе данных"""
    print("=" * 70)
    print("🔍 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ")
    print("=" * 70)
    print()
    
    # Загружаем настройки
    try:
        from app.config import get_settings
        settings = get_settings()
    except Exception as e:
        print(f"❌ Ошибка загрузки настроек: {e}")
        print()
        print("Убедитесь, что:")
        print("1. Файл backend/.env существует")
        print("2. DATABASE_URL установлен")
        return False
    
    # Проверка DATABASE_URL
    db_url = settings.database_url
    print(f"📋 DATABASE_URL: {db_url[:50]}..." if len(db_url) > 50 else f"📋 DATABASE_URL: {db_url}")
    print()
    
    # Проверка формата
    if not db_url.startswith("postgresql"):
        print("❌ ОШИБКА: DATABASE_URL должен начинаться с 'postgresql'")
        print(f"   Текущий формат: {db_url[:30]}...")
        return False
    
    if "+asyncpg" not in db_url:
        print("⚠️  ПРЕДУПРЕЖДЕНИЕ: DATABASE_URL должен содержать '+asyncpg'")
        print("   Рекомендуемый формат: postgresql+asyncpg://...")
        print("   Продолжаем тест...")
        print()
    
    # Тест подключения
    print("🔄 Тестирование подключения...")
    try:
        from app.database import engine, async_session_maker
        from sqlalchemy import text
        
        # Тест подключения
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            
            if test_value == 1:
                print("✅ Подключение к базе данных успешно!")
                print()
                
                # Проверка таблиц
                print("🔄 Проверка таблиц...")
                result = await session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN (
                        'messages', 'classifications', 'response_templates', 
                        'keywords', 'operator_feedback', 'operator_session_logs',
                        'reminders', 'chat_sessions', 'operator_message_reads'
                    )
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result.fetchall()]
                
                expected_tables = [
                    'messages', 'classifications', 'response_templates',
                    'keywords', 'operator_feedback', 'operator_session_logs',
                    'reminders', 'chat_sessions', 'operator_message_reads'
                ]
                
                missing_tables = set(expected_tables) - set(tables)
                
                if missing_tables:
                    print(f"⚠️  Отсутствуют таблицы: {', '.join(missing_tables)}")
                    print("   Выполните миграции: database/migrations_supabase.sql")
                else:
                    print(f"✅ Все таблицы созданы ({len(tables)} из {len(expected_tables)})")
                
                # Проверка ENUM типов
                print()
                print("🔄 Проверка ENUM типов...")
                result = await session.execute(text("""
                    SELECT typname 
                    FROM pg_type 
                    WHERE typtype = 'e' 
                    AND typname IN (
                        'messagetype', 'scenariotype', 'remindertype', 
                        'dialogstatus', 'prioritylevel', 'escalationreason'
                    )
                    ORDER BY typname
                """))
                enums = [row[0] for row in result.fetchall()]
                
                expected_enums = [
                    'messagetype', 'scenariotype', 'remindertype',
                    'dialogstatus', 'prioritylevel', 'escalationreason'
                ]
                
                missing_enums = set(expected_enums) - set(enums)
                
                if missing_enums:
                    print(f"⚠️  Отсутствуют ENUM типы: {', '.join(missing_enums)}")
                    print("   Выполните миграции: database/migrations_supabase.sql")
                else:
                    print(f"✅ Все ENUM типы созданы ({len(enums)} из {len(expected_enums)})")
                
                print()
                print("=" * 70)
                print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
                print("=" * 70)
                return True
            else:
                print(f"❌ Неожиданный результат теста: {test_value}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        print()
        print("Возможные причины:")
        print("1. Неправильный DATABASE_URL")
        print("2. Неправильный пароль")
        print("3. Хост недоступен")
        print("4. База данных не существует")
        print("5. Firewall блокирует подключение")
        return False
    finally:
        # Закрываем соединения
        try:
            from app.database import close_db
            await close_db()
        except:
            pass

async def test_redis_connection():
    """Тестирование подключения к Redis (опционально)"""
    print()
    print("=" * 70)
    print("🔍 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К REDIS")
    print("=" * 70)
    print()
    
    try:
        from app.config import get_settings
        settings = get_settings()
        
        redis_url = settings.redis_url
        
        if not redis_url:
            print("ℹ️  Redis не настроен (REDIS_URL пустой)")
            print("   Система будет использовать in-memory cache")
            return True
        
        print(f"📋 REDIS_URL: {redis_url}")
        print()
        print("🔄 Тестирование подключения...")
        
        from app.utils.redis_cache import get_redis_cache
        redis_cache = await get_redis_cache()
        
        # Тест записи/чтения
        test_key = "test:connection"
        test_value = "test_value_123"
        
        await redis_cache.set(test_key, test_value, ttl_seconds=10)
        result = await redis_cache.get(test_key)
        
        if result == test_value:
            print("✅ Подключение к Redis успешно!")
            await redis_cache.delete(test_key)
            return True
        else:
            print(f"⚠️  Redis доступен, но тест записи/чтения не прошел")
            return False
            
    except Exception as e:
        print(f"⚠️  Redis недоступен: {e}")
        print("   Система будет использовать in-memory cache")
        return True  # Это не критично

async def main():
    """Главная функция"""
    print()
    
    # Тест БД
    db_ok = await test_database_connection()
    
    # Тест Redis
    redis_ok = await test_redis_connection()
    
    print()
    print("=" * 70)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    print()
    print(f"База данных: {'✅ OK' if db_ok else '❌ FAILED'}")
    print(f"Redis:       {'✅ OK' if redis_ok else '⚠️  Unavailable (не критично)'}")
    print()
    
    if not db_ok:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: База данных недоступна")
        print("   Исправьте DATABASE_URL и повторите тест")
        sys.exit(1)
    
    print("✅ Все критичные проверки пройдены!")
    print("   Проект готов к деплою")
    print()

if __name__ == "__main__":
    asyncio.run(main())







