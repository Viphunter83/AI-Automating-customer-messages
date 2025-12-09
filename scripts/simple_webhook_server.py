#!/usr/bin/env python3
"""
Простой webhook сервер для тестирования интеграции
Использование: python scripts/simple_webhook_server.py

Этот сервер имитирует ваш CRM webhook endpoint для приема ответов от AI системы.
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# Хранилище полученных webhook запросов
received_webhooks = []


@app.route('/webhook', methods=['POST'])
def receive_webhook():
    """Endpoint для приема webhook запросов от AI системы"""
    try:
        data = request.json
        
        # Логируем полученный запрос
        webhook_data = {
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "headers": dict(request.headers)
        }
        received_webhooks.append(webhook_data)
        
        # Извлекаем данные
        client_id = data.get('client_id', 'N/A')
        response_text = data.get('response_text', 'N/A')
        scenario = data.get('classification', {}).get('scenario', 'N/A')
        confidence = data.get('classification', {}).get('confidence', 'N/A')
        requires_escalation = data.get('requires_escalation', False)
        
        # Выводим информацию
        print("\n" + "=" * 70)
        print(f"📥 ПОЛУЧЕН WEBHOOK ЗАПРОС")
        print("=" * 70)
        print(f"Время: {webhook_data['timestamp']}")
        print(f"Client ID: {client_id}")
        print(f"Scenario: {scenario}")
        print(f"Confidence: {confidence}")
        print(f"Escalation: {requires_escalation}")
        print(f"\nResponse Text:")
        print(f"  {response_text}")
        print("=" * 70)
        
        # Здесь вы бы отправили ответ клиенту в вашей CRM системе
        # TODO: Реализуйте отправку сообщения клиенту
        
        # Возвращаем успешный ответ
        return jsonify({
            "ok": True,
            "message_id": f"crm_msg_{datetime.now().timestamp()}",
            "received_at": webhook_data['timestamp']
        }), 200
        
    except Exception as e:
        print(f"\n❌ Ошибка при обработке webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route('/webhooks/received', methods=['GET'])
def list_received_webhooks():
    """Просмотр всех полученных webhook запросов"""
    return jsonify({
        "count": len(received_webhooks),
        "webhooks": received_webhooks
    }), 200


@app.route('/webhooks/clear', methods=['POST'])
def clear_webhooks():
    """Очистить список полученных webhook запросов"""
    global received_webhooks
    count = len(received_webhooks)
    received_webhooks = []
    return jsonify({
        "ok": True,
        "cleared": count
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "webhooks_received": len(received_webhooks)
    }), 200


if __name__ == '__main__':
    print("=" * 70)
    print("🚀 ЗАПУСК ПРОСТОГО WEBHOOK СЕРВЕРА ДЛЯ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    print("\nСервер будет доступен по адресу:")
    print("  http://localhost:5000/webhook")
    print("\nДля локального тестирования используйте ngrok:")
    print("  ngrok http 5000")
    print("\nПосле запуска ngrok используйте полученный URL как X-Webhook-URL")
    print("\n" + "=" * 70)
    print("Нажмите Ctrl+C для остановки сервера")
    print("=" * 70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)







