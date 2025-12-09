#!/bin/bash

# Скрипт для автоматической установки и запуска ngrok

set -e

echo "🔍 Проверка ngrok..."

# Проверяем, установлен ли ngrok
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok уже установлен"
    NGROK_CMD="ngrok"
else
    echo "📥 Установка ngrok..."
    
    # Создаем директорию для бинарников
    mkdir -p ~/.local/bin
    export PATH="$HOME/.local/bin:$PATH"
    
    # Скачиваем ngrok для macOS ARM64
    cd /tmp
    curl -L https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-darwin-arm64.tgz -o ngrok.tgz
    
    # Распаковываем
    tar -xzf ngrok.tgz
    chmod +x ngrok
    mv ngrok ~/.local/bin/ngrok
    
    # Проверяем установку
    if [ -f ~/.local/bin/ngrok ]; then
        echo "✅ ngrok установлен в ~/.local/bin/ngrok"
        NGROK_CMD="$HOME/.local/bin/ngrok"
    else
        echo "❌ Ошибка установки ngrok"
        echo "📖 Пожалуйста, установите ngrok вручную:"
        echo "   brew install ngrok/ngrok/ngrok"
        echo "   или скачайте с https://ngrok.com/download"
        exit 1
    fi
fi

echo ""
echo "🚀 Запуск ngrok на порту 8000..."
echo ""

# Запускаем ngrok в фоне
$NGROK_CMD http 8000 > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Ждем запуска
sleep 3

# Получаем URL через ngrok API
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$NGROK_URL" ]; then
    echo "⚠️  Не удалось получить URL от ngrok"
    echo "📋 Проверьте логи: tail -f /tmp/ngrok.log"
    echo "📋 Или откройте http://localhost:4040 в браузере"
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi

# Убираем https:// из URL для использования в файлах
NGROK_HOST=$(echo $NGROK_URL | sed 's|https://||')

echo "✅ ngrok запущен!"
echo "🌐 Публичный URL: $NGROK_URL"
echo "📝 Host: $NGROK_HOST"
echo ""
echo "💾 Сохранение информации..."

# Сохраняем информацию в файл
cat > /tmp/ngrok_info.txt << EOF
NGROK_URL=$NGROK_URL
NGROK_HOST=$NGROK_HOST
NGROK_PID=$NGROK_PID
EOF

echo "✅ Информация сохранена в /tmp/ngrok_info.txt"
echo ""
echo "📋 PID процесса ngrok: $NGROK_PID"
echo "🛑 Для остановки: kill $NGROK_PID"
echo ""
echo "🎉 Готово! Используйте URL: $NGROK_URL"







