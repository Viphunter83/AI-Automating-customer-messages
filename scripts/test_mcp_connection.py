#!/usr/bin/env python3
"""
Скрипт для проверки доступности MCP для Supabase
"""
import os
import sys
import httpx
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


async def test_mcp_connection():
    """Тестирование подключения к MCP"""
    print("=" * 70)
    print("🔍 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К MCP")
    print("=" * 70)
    print()
    
    # Загружаем настройки
    try:
        from app.config import get_settings
        settings = get_settings()
    except Exception as e:
        print(f"❌ Ошибка загрузки настроек: {e}")
        return False
    
    # Получаем параметры
    supabase_url = settings.supabase_url or os.getenv("SUPABASE_URL", "")
    supabase_key = settings.supabase_key or os.getenv("SUPABASE_KEY", "")
    
    if not supabase_url:
        print("❌ SUPABASE_URL не установлен")
        print()
        print("Установите SUPABASE_URL:")
        print("  - Для Kong Gateway: http://kong:8000")
        print("  - Для внешнего доступа: https://supabase.neiroaleksandra.dev.zerocoder.pro")
        return False
    
    if not supabase_key:
        print("⚠️  SUPABASE_KEY не установлен")
        print("   MCP может требовать аутентификацию")
        print()
    
    # Формируем MCP URL
    mcp_url = f"{supabase_url.rstrip('/')}/mcp"
    
    print(f"📋 SUPABASE_URL: {supabase_url}")
    print(f"📋 MCP URL: {mcp_url}")
    print(f"📋 SUPABASE_KEY: {'***' if supabase_key else 'не установлен'}")
    print()
    
    # Тест подключения
    print("🔄 Тестирование подключения...")
    
    headers = {}
    if supabase_key:
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
        }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Проверка базового доступа
            response = await client.get(mcp_url, headers=headers)
            
            print(f"📊 HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ MCP доступен!")
                print()
                print("📄 Ответ:")
                try:
                    data = response.json()
                    print(f"   {data}")
                except:
                    print(f"   {response.text[:200]}")
                return True
            elif response.status_code == 404:
                print("⚠️  MCP endpoint не найден (404)")
                print()
                print("Возможные причины:")
                print("  1. MCP не включен в Supabase конфигурации")
                print("  2. Неправильный URL (должен быть /mcp)")
                print("  3. Kong Gateway не настроен для MCP")
                return False
            elif response.status_code == 401:
                print("❌ Ошибка аутентификации (401)")
                print()
                print("Проверьте:")
                print("  1. Правильность SUPABASE_KEY")
                print("  2. Права доступа к MCP")
                return False
            else:
                print(f"❌ Неожиданный статус: {response.status_code}")
                print(f"   Ответ: {response.text[:200]}")
                return False
                
    except httpx.ConnectError as e:
        print(f"❌ Ошибка подключения: {e}")
        print()
        print("Проверьте:")
        print("  1. Доступность SUPABASE_URL")
        print("  2. Правильность адреса (http://kong:8000 или внешний URL)")
        print("  3. Сеть Docker (если используется внутренний адрес)")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


async def main():
    """Главная функция"""
    import asyncio
    
    print()
    success = await test_mcp_connection()
    
    print()
    print("=" * 70)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    print()
    
    if success:
        print("✅ MCP доступен и готов к использованию!")
        print()
        print("📋 Следующие шаги:")
        print("  1. Добавьте MCP сервер в Cursor:")
        print(f"     URL: {os.getenv('SUPABASE_URL', 'http://kong:8000')}/mcp")
        print("  2. Используйте переменные окружения для ключей")
        print("  3. Начните использовать MCP для работы с БД")
    else:
        print("❌ MCP недоступен")
        print()
        print("📋 Что проверить:")
        print("  1. Убедитесь, что MCP включен в Supabase")
        print("  2. Проверьте правильность SUPABASE_URL")
        print("  3. Проверьте SUPABASE_KEY (если требуется)")
        print("  4. См. dokploy/MCP_SUPABASE_SETUP.md для деталей")
    
    print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())







