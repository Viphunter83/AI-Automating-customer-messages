#!/bin/bash

# Скрипт для проверки backend URL и готовности к интеграции
# Использование: ./scripts/check_backend_url.sh https://your-backend-url.com

set -e

BACKEND_URL="${1:-http://localhost:8000}"

echo "=" | tr -d '\n' && printf '%.0s=' {1..69} && echo ""
echo "  ПРОВЕРКА BACKEND URL ДЛЯ ИНТЕГРАЦИИ С N8N"
echo "=" | tr -d '\n' && printf '%.0s=' {1..69} && echo ""
echo ""
echo "Backend URL: $BACKEND_URL"
echo ""

# Проверка health endpoint
echo "1. Проверка health endpoint..."
HEALTH_URL="$BACKEND_URL/api/health"
if curl -s -f "$HEALTH_URL" > /dev/null; then
    echo "   ✅ Health check успешен"
    HEALTH_RESPONSE=$(curl -s "$HEALTH_URL")
    echo "   Ответ: $HEALTH_RESPONSE"
else
    echo "   ❌ Health check не прошел"
    echo "   Проверьте, что backend запущен и доступен"
    exit 1
fi

echo ""

# Проверка messages endpoint
echo "2. Проверка messages endpoint..."
MESSAGES_URL="$BACKEND_URL/api/messages/"
TEST_PAYLOAD='{"client_id":"test_check_001","content":"Тестовая проверка"}'

if curl -s -f -X POST "$MESSAGES_URL" \
    -H "Content-Type: application/json" \
    -H "X-Webhook-URL: https://test-webhook.com/test" \
    -d "$TEST_PAYLOAD" > /dev/null; then
    echo "   ✅ Messages endpoint доступен"
    
    # Получить ответ
    RESPONSE=$(curl -s -X POST "$MESSAGES_URL" \
        -H "Content-Type: application/json" \
        -H "X-Webhook-URL: https://test-webhook.com/test" \
        -d "$TEST_PAYLOAD")
    
    echo "   Ответ получен:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo "   ❌ Messages endpoint не доступен"
    echo "   Проверьте логи backend"
    exit 1
fi

echo ""
echo "=" | tr -d '\n' && printf '%.0s=' {1..69} && echo ""
echo "✅ BACKEND ГОТОВ К ИНТЕГРАЦИИ!"
echo "=" | tr -d '\n' && printf '%.0s=' {1..69} && echo ""
echo ""
echo "API URL для заказчика:"
echo "  POST $MESSAGES_URL"
echo ""
echo "Следующие шаги:"
echo "  1. Замените НАШ_BACKEND_URL в файле БЫСТРЫЙ_СТАРТ_N8N.md"
echo "  2. Отправьте файл заказчику"
echo ""







