#!/bin/bash

# Тестирование Railway API
# Использование: ./test_railway_api.sh YOUR_RAILWAY_URL

RAILWAY_URL="${1:-}"

if [ -z "$RAILWAY_URL" ]; then
    echo "❌ Ошибка: Укажите Railway URL"
    echo "Использование: ./test_railway_api.sh https://your-app.railway.app"
    echo ""
    echo "Railway URL можно найти в:"
    echo "  - Railway Dashboard → Сервис приложения → Settings → Domains"
    echo "  - Или в Deploy Logs"
    exit 1
fi

echo "🧪 Тестирование Railway API: $RAILWAY_URL"
echo ""

# 1. Health Check
echo "1️⃣ Тестирование /health..."
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$RAILWAY_URL/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$HEALTH_RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check успешен!"
    echo "Ответ: $BODY"
else
    echo "❌ Health check не прошел (HTTP $HTTP_CODE)"
    echo "Ответ: $BODY"
fi
echo ""

# 2. Full Health Check
echo "2️⃣ Тестирование /health/full..."
FULL_HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$RAILWAY_URL/health/full")
HTTP_CODE=$(echo "$FULL_HEALTH_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$FULL_HEALTH_RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Full health check успешен!"
    echo "Ответ: $BODY" | head -20
else
    echo "❌ Full health check не прошел (HTTP $HTTP_CODE)"
    echo "Ответ: $BODY"
fi
echo ""

# 3. Create Message
echo "3️⃣ Тестирование создания сообщения..."
CREATE_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -X POST "$RAILWAY_URL/api/messages/" \
    -H "Content-Type: application/json" \
    -d '{
        "client_id": "test_client_'$(date +%s)'",
        "content": "Привет! Мне нужна помощь с настройкой"
    }')
HTTP_CODE=$(echo "$CREATE_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$CREATE_RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "201" ]; then
    echo "✅ Создание сообщения успешно!"
    echo "Ответ: $BODY" | head -30
else
    echo "❌ Создание сообщения не прошло (HTTP $HTTP_CODE)"
    echo "Ответ: $BODY"
fi
echo ""

echo "✅ Тестирование завершено!"

