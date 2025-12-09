#!/bin/bash

# Автоматическая подготовка интеграции с n8n

set -e

GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
RESET='\033[0m'

echo -e "${BLUE}======================================================================${RESET}"
echo -e "${BLUE}🚀 АВТОМАТИЧЕСКАЯ ПОДГОТОВКА ИНТЕГРАЦИИ С N8N${RESET}"
echo -e "${BLUE}======================================================================${RESET}\n"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Шаг 1: Проверка Docker
echo -e "${BLUE}▶ Шаг 1:${RESET} Проверка Docker контейнеров..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Docker контейнеры запущены${RESET}"
else
    echo -e "${YELLOW}⚠️  Запускаю Docker контейнеры...${RESET}"
    docker-compose up -d
    sleep 5
fi

# Шаг 2: Проверка backend
echo -e "\n${BLUE}▶ Шаг 2:${RESET} Проверка backend..."
if curl -s http://localhost:8000/health > /dev/null 2>&1 || curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend работает на http://localhost:8000${RESET}"
else
    echo -e "${YELLOW}⚠️  Backend не отвечает, но продолжаем...${RESET}"
fi

# Шаг 3: Проверка/установка ngrok
echo -e "\n${BLUE}▶ Шаг 3:${RESET} Проверка ngrok..."

NGROK_CMD=""
if command -v ngrok &> /dev/null; then
    NGROK_CMD="ngrok"
    echo -e "${GREEN}✅ ngrok установлен${RESET}"
elif [ -f ~/.local/bin/ngrok ]; then
    NGROK_CMD="$HOME/.local/bin/ngrok"
    echo -e "${GREEN}✅ ngrok найден в ~/.local/bin/ngrok${RESET}"
else
    echo -e "${YELLOW}⚠️  ngrok не установлен${RESET}"
    echo -e "${YELLOW}📥 Попытка установки через brew...${RESET}"
    
    if command -v brew &> /dev/null; then
        brew install ngrok/ngrok/ngrok 2>&1 | grep -v "Already installed" || true
        if command -v ngrok &> /dev/null; then
            NGROK_CMD="ngrok"
            echo -e "${GREEN}✅ ngrok установлен${RESET}"
        fi
    fi
    
    if [ -z "$NGROK_CMD" ]; then
        echo -e "${YELLOW}⚠️  Автоматическая установка не удалась${RESET}"
        echo -e "${YELLOW}📋 Установите ngrok вручную:${RESET}"
        echo -e "   brew install ngrok/ngrok/ngrok"
        echo -e "   или скачайте: https://ngrok.com/download"
        echo -e "\n${YELLOW}После установки запустите этот скрипт снова${RESET}"
        exit 1
    fi
fi

# Шаг 4: Запуск ngrok
echo -e "\n${BLUE}▶ Шаг 4:${RESET} Запуск ngrok..."

# Проверяем, не запущен ли уже ngrok
if pgrep -f "ngrok http 8000" > /dev/null; then
    echo -e "${GREEN}✅ ngrok уже запущен${RESET}"
else
    echo -e "${YELLOW}🚀 Запускаю ngrok в фоне...${RESET}"
    $NGROK_CMD http 8000 > /tmp/ngrok.log 2>&1 &
    NGROK_PID=$!
    echo $NGROK_PID > /tmp/ngrok.pid
    sleep 3
    echo -e "${GREEN}✅ ngrok запущен (PID: $NGROK_PID)${RESET}"
fi

# Шаг 5: Получение URL
echo -e "\n${BLUE}▶ Шаг 5:${RESET} Получение публичного URL..."

sleep 2
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$NGROK_URL" ]; then
    echo -e "${YELLOW}⚠️  Не удалось получить URL автоматически${RESET}"
    echo -e "${YELLOW}📋 Откройте http://localhost:4040 в браузере и скопируйте HTTPS URL${RESET}"
    echo -e "${YELLOW}Затем запустите:${RESET}"
    echo -e "   python3 scripts/prepare_n8n_integration.py <ваш-ngrok-url>"
    exit 1
fi

NGROK_HOST=$(echo $NGROK_URL | sed 's|https://||' | sed 's|/$||')
echo -e "${GREEN}✅ Получен URL: $NGROK_URL${RESET}"
echo -e "${GREEN}✅ Host: $NGROK_HOST${RESET}"

# Шаг 6: Обновление файлов
echo -e "\n${BLUE}▶ Шаг 6:${RESET} Обновление файлов..."

python3 scripts/prepare_n8n_integration.py "$NGROK_HOST"

# Шаг 7: Тестирование
echo -e "\n${BLUE}▶ Шаг 7:${RESET} Тестирование API..."

if curl -s "$NGROK_URL/health" > /dev/null 2>&1 || curl -s "$NGROK_URL/" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API доступен через ngrok${RESET}"
else
    echo -e "${YELLOW}⚠️  API пока не отвечает через ngrok (может потребоваться время)${RESET}"
fi

# Итог
echo -e "\n${GREEN}======================================================================${RESET}"
echo -e "${GREEN}✅ ВСЁ ГОТОВО!${RESET}"
echo -e "${GREEN}======================================================================${RESET}\n"
echo -e "${BLUE}📧 Отправьте заказчику:${RESET}"
echo -e "   - Backend API URL: POST $NGROK_URL/api/messages/"
echo -e "   - Файл: БЫСТРЫЙ_СТАРТ_N8N.md"
echo -e "\n${YELLOW}⚠️  Важно:${RESET}"
echo -e "   - ngrok должен быть запущен пока идет тестирование"
echo -e "   - Для остановки: kill \$(cat /tmp/ngrok.pid)"
echo -e "   - URL изменится при перезапуске ngrok (бесплатный план)"
echo -e "\n${GREEN}🎉 Готово к интеграции!${RESET}\n"







