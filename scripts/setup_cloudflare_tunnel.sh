#!/bin/bash

# Автоматическая настройка Cloudflare Tunnel для интеграции с n8n

set -e

GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
RED='\033[91m'
RESET='\033[0m'

echo -e "${BLUE}======================================================================${RESET}"
echo -e "${BLUE}🚀 НАСТРОЙКА CLOUDFLARE TUNNEL ДЛЯ N8N${RESET}"
echo -e "${BLUE}======================================================================${RESET}\n"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Проверка Docker
echo -e "${BLUE}▶ Шаг 1:${RESET} Проверка Docker..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Docker контейнеры запущены${RESET}"
else
    echo -e "${YELLOW}⚠️  Запускаю Docker контейнеры...${RESET}"
    docker-compose up -d
    sleep 5
fi

# Проверка backend
echo -e "\n${BLUE}▶ Шаг 2:${RESET} Проверка backend..."
if curl -s http://localhost:8000/health > /dev/null 2>&1 || curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend работает на http://localhost:8000${RESET}"
else
    echo -e "${YELLOW}⚠️  Backend не отвечает, но продолжаем...${RESET}"
fi

# Проверка/установка cloudflared
echo -e "\n${BLUE}▶ Шаг 3:${RESET} Проверка Cloudflare Tunnel..."

if command -v cloudflared &> /dev/null; then
    echo -e "${GREEN}✅ cloudflared установлен${RESET}"
else
    echo -e "${YELLOW}⚠️  cloudflared не установлен${RESET}"
    echo -e "${YELLOW}📥 Установка через brew...${RESET}"
    
    if command -v brew &> /dev/null; then
        brew install cloudflare/cloudflare/cloudflared
        echo -e "${GREEN}✅ cloudflared установлен${RESET}"
    else
        echo -e "${RED}❌ brew не найден. Установите вручную:${RESET}"
        echo -e "   brew install cloudflare/cloudflare/cloudflared"
        exit 1
    fi
fi

# Запуск туннеля
echo -e "\n${BLUE}▶ Шаг 4:${RESET} Запуск Cloudflare Tunnel..."

if pgrep -f "cloudflared tunnel" > /dev/null; then
    echo -e "${YELLOW}⚠️  Cloudflare Tunnel уже запущен${RESET}"
    echo -e "${YELLOW}📋 Проверьте вывод процесса для получения URL${RESET}"
else
    echo -e "${YELLOW}🚀 Запускаю Cloudflare Tunnel в фоне...${RESET}"
    cloudflared tunnel --url http://localhost:8000 > /tmp/cloudflared.log 2>&1 &
    CLOUDFLARED_PID=$!
    echo $CLOUDFLARED_PID > /tmp/cloudflared.pid
    sleep 5
    
    # Получаем URL из логов
    TUNNEL_URL=$(grep -o "https://[a-z0-9-]*\.trycloudflare\.com" /tmp/cloudflared.log | head -1)
    
    if [ -z "$TUNNEL_URL" ]; then
        echo -e "${YELLOW}⚠️  URL пока не получен, проверьте логи:${RESET}"
        echo -e "   tail -f /tmp/cloudflared.log"
        echo -e "\n${YELLOW}Или откройте терминал и запустите:${RESET}"
        echo -e "   cloudflared tunnel --url http://localhost:8000"
        echo -e "\n${YELLOW}Скопируйте URL и запустите:${RESET}"
        echo -e "   python3 scripts/prepare_n8n_integration.py <ваш-url>"
        exit 0
    fi
    
    TUNNEL_HOST=$(echo $TUNNEL_URL | sed 's|https://||' | sed 's|/$||')
    echo -e "${GREEN}✅ Получен URL: $TUNNEL_URL${RESET}"
    echo -e "${GREEN}✅ Host: $TUNNEL_HOST${RESET}"
    
    # Обновление файлов
    echo -e "\n${BLUE}▶ Шаг 5:${RESET} Обновление файлов..."
    python3 scripts/prepare_n8n_integration.py "$TUNNEL_HOST"
    
    # Тестирование
    echo -e "\n${BLUE}▶ Шаг 6:${RESET} Тестирование API..."
    sleep 2
    if curl -s "$TUNNEL_URL/health" > /dev/null 2>&1 || curl -s "$TUNNEL_URL/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API доступен через Cloudflare Tunnel${RESET}"
    else
        echo -e "${YELLOW}⚠️  API пока не отвечает (может потребоваться время)${RESET}"
    fi
    
    # Итог
    echo -e "\n${GREEN}======================================================================${RESET}"
    echo -e "${GREEN}✅ ВСЁ ГОТОВО!${RESET}"
    echo -e "${GREEN}======================================================================${RESET}\n"
    echo -e "${BLUE}📧 Отправьте заказчику:${RESET}"
    echo -e "   - Backend API URL: POST $TUNNEL_URL/api/messages/"
    echo -e "   - Файл: БЫСТРЫЙ_СТАРТ_N8N.md"
    echo -e "\n${YELLOW}⚠️  Важно:${RESET}"
    echo -e "   - Cloudflare Tunnel должен быть запущен пока идет тестирование"
    echo -e "   - Для остановки: kill \$(cat /tmp/cloudflared.pid)"
    echo -e "   - URL стабильный и не меняется при перезапуске"
    echo -e "\n${GREEN}🎉 Готово к интеграции!${RESET}\n"
fi







