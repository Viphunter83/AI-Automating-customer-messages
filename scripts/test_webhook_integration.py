#!/usr/bin/env python3
"""
Скрипт для тестирования webhook интеграции
Использование: python scripts/test_webhook_integration.py
"""

import requests
import json
import time
import sys
from datetime import datetime

# Конфигурация
API_URL = "http://localhost:8000/api/messages/"  # Измените на ваш URL
WEBHOOK_URL = "http://localhost:5000/webhook"  # Измените на ваш webhook URL
PLATFORM = "test"

# Тестовые сценарии
TEST_SCENARIOS = [
    {
        "name": "Приветствие",
        "client_id": "test_client_001",
        "content": "Привет! Я новый клиент"
    },
    {
        "name": "Пропуск занятий",
        "client_id": "test_client_002",
        "content": "Мне нужно пропустить занятие завтра, болею"
    },
    {
        "name": "Техническая поддержка",
        "client_id": "test_client_003",
        "content": "Не могу зайти в личный кабинет, выдает ошибку"
    },
    {
        "name": "Реферальная программа",
        "client_id": "test_client_004",
        "content": "Хочу узнать про реферальную программу"
    },
    {
        "name": "Жалоба (эскалация)",
        "client_id": "test_client_005",
        "content": "Я очень недоволен качеством занятий"
    }
]


def print_section(title):
    """Печать заголовка секции"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def send_message(scenario):
    """Отправка сообщения в систему"""
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-URL": WEBHOOK_URL,
        "X-Platform": PLATFORM
    }
    
    data = {
        "client_id": scenario["client_id"],
        "content": scenario["content"]
    }
    
    try:
        print(f"\n📤 Отправка сообщения: {scenario['name']}")
        print(f"   Client ID: {scenario['client_id']}")
        print(f"   Content: {scenario['content']}")
        
        response = requests.post(API_URL, json=data, headers=headers, timeout=30)
        
        print(f"\n📥 Ответ от API:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"   Status: {result.get('status')}")
            print(f"   Scenario: {result.get('classification', {}).get('scenario', 'N/A')}")
            print(f"   Confidence: {result.get('classification', {}).get('confidence', 'N/A')}")
            print(f"   Response Text: {result.get('response', {}).get('text', 'N/A')[:100]}...")
            print(f"   Escalation: {result.get('requires_escalation', False)}")
            print(f"   Priority: {result.get('priority', 'N/A')}")
            
            return True, result
        else:
            print(f"   Error: {response.text}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ошибка при отправке: {e}")
        return False, None


def test_webhook_receiver():
    """Тест получения webhook (имитация)"""
    print("\n⚠️  Примечание: Убедитесь, что ваш webhook сервер запущен и доступен")
    print(f"   Webhook URL: {WEBHOOK_URL}")
    print("\n   Webhook должен быть доступен по адресу выше")
    print("   Используйте ngrok для локального тестирования: ngrok http 5000")


def main():
    """Основная функция"""
    print_section("ТЕСТИРОВАНИЕ WEBHOOK ИНТЕГРАЦИИ")
    
    print(f"\nКонфигурация:")
    print(f"  API URL: {API_URL}")
    print(f"  Webhook URL: {WEBHOOK_URL}")
    print(f"  Platform: {PLATFORM}")
    
    # Проверка доступности API
    print_section("Проверка доступности API")
    try:
        health_response = requests.get(API_URL.replace("/api/messages/", "/health"), timeout=5)
        if health_response.status_code == 200:
            print("✅ API доступен")
        else:
            print(f"⚠️  API вернул статус {health_response.status_code}")
    except Exception as e:
        print(f"❌ API недоступен: {e}")
        print("\nУбедитесь, что backend запущен и доступен по адресу:", API_URL)
        sys.exit(1)
    
    # Информация о webhook
    test_webhook_receiver()
    
    # Тестирование сценариев
    print_section("Тестирование сценариев")
    
    results = []
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"\n--- Тест {i}/{len(TEST_SCENARIOS)} ---")
        success, result = send_message(scenario)
        results.append({
            "scenario": scenario["name"],
            "success": success,
            "result": result
        })
        
        # Пауза между запросами (чтобы не превысить rate limit)
        if i < len(TEST_SCENARIOS):
            print("\n⏳ Пауза 2 секунды перед следующим тестом...")
            time.sleep(2)
    
    # Итоги
    print_section("Итоги тестирования")
    
    successful = sum(1 for r in results if r["success"])
    print(f"\nУспешно: {successful}/{len(results)}")
    
    print("\nДетали:")
    for r in results:
        status = "✅" if r["success"] else "❌"
        scenario_name = r["scenario"]
        if r["success"]:
            scenario_type = r["result"].get("classification", {}).get("scenario", "N/A")
            print(f"  {status} {scenario_name} -> {scenario_type}")
        else:
            print(f"  {status} {scenario_name} -> Ошибка")
    
    print("\n" + "=" * 70)
    print("✅ Тестирование завершено!")
    print("\nПроверьте ваш webhook endpoint - вы должны были получить")
    print("ответы от системы на адрес:", WEBHOOK_URL)
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)







