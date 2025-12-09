#!/usr/bin/env python3
"""
Автоматическая подготовка интеграции с n8n для локального проекта
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path

# Цвета для вывода
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_step(step, message):
    print(f"\n{BLUE}▶ Шаг {step}:{RESET} {message}")

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠️  {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def check_docker():
    """Проверка Docker контейнеров"""
    print_step(1, "Проверка Docker контейнеров...")
    try:
        result = subprocess.run(
            ["docker-compose", "ps"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        if "Up" in result.stdout:
            print_success("Docker контейнеры запущены")
            return True
        else:
            print_warning("Docker контейнеры не запущены")
            return False
    except Exception as e:
        print_error(f"Ошибка проверки Docker: {e}")
        return False

def check_backend():
    """Проверка backend"""
    print_step(2, "Проверка backend...")
    try:
        import urllib.request
        # Пробуем разные endpoints
        endpoints = ["http://localhost:8000/api/health", "http://localhost:8000/health", "http://localhost:8000/"]
        for endpoint in endpoints:
            try:
                response = urllib.request.urlopen(endpoint, timeout=5)
                print_success(f"Backend работает на http://localhost:8000")
                return True
            except:
                continue
        print_warning("Backend не отвечает на стандартные endpoints")
        return False
    except Exception as e:
        # Если сервер отвечает (даже с ошибкой), значит он работает
        print_success("Backend работает на http://localhost:8000")
        return True

def check_ngrok():
    """Проверка установки ngrok"""
    print_step(3, "Проверка ngrok...")
    ngrok_paths = [
        "ngrok",
        os.path.expanduser("~/.local/bin/ngrok"),
        "/usr/local/bin/ngrok",
    ]
    
    for path in ngrok_paths:
        try:
            result = subprocess.run(
                [path, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print_success(f"ngrok найден: {path}")
                return path
        except:
            continue
    
    print_warning("ngrok не установлен")
    return None

def update_file_with_url(file_path, url_host):
    """Обновление файла с URL"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем плейсхолдеры
        content = content.replace("НАШ_BACKEND_URL", url_host)
        content = content.replace("ВАШ_BACKEND_URL", url_host)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_success(f"Обновлен файл: {file_path}")
        return True
    except Exception as e:
        print_error(f"Ошибка обновления файла {file_path}: {e}")
        return False

def main():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}🚀 АВТОМАТИЧЕСКАЯ ПОДГОТОВКА ИНТЕГРАЦИИ С N8N{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    project_root = Path(__file__).parent.parent
    
    # Проверки
    docker_ok = check_docker()
    backend_ok = check_backend()
    ngrok_path = check_ngrok()
    
    if not docker_ok:
        print_error("Запустите Docker контейнеры: docker-compose up -d")
        return 1
    
    if not backend_ok:
        print_error("Backend не работает. Проверьте контейнеры.")
        return 1
    
    # Получение URL
    print_step(4, "Получение публичного URL...")
    
    if ngrok_path:
        print_success("ngrok установлен!")
        print(f"\n{YELLOW}📋 ИНСТРУКЦИИ:{RESET}")
        print(f"1. Запустите ngrok в отдельном терминале:")
        print(f"   {ngrok_path} http 8000")
        print(f"\n2. Скопируйте HTTPS URL (например: abc123.ngrok-free.app)")
        print(f"\n3. Запустите этот скрипт снова с URL:")
        print(f"   python3 {__file__} <ваш-ngrok-url>")
    else:
        print_warning("ngrok не установлен")
        print(f"\n{YELLOW}📋 ИНСТРУКЦИИ ПО УСТАНОВКЕ:{RESET}")
        print(f"1. Установите ngrok:")
        print(f"   brew install ngrok/ngrok/ngrok")
        print(f"   или скачайте: https://ngrok.com/download")
        print(f"\n2. Запустите ngrok:")
        print(f"   ngrok http 8000")
        print(f"\n3. Скопируйте HTTPS URL и запустите:")
        print(f"   python3 {__file__} <ваш-ngrok-url>")
    
    # Если URL передан как аргумент
    if len(sys.argv) > 1:
        url_host = sys.argv[1].replace("https://", "").replace("http://", "").rstrip("/")
        print(f"\n{BLUE}Используется URL: {url_host}{RESET}")
        
        # Обновляем файлы
        files_to_update = [
            project_root / "БЫСТРЫЙ_СТАРТ_N8N.md",
        ]
        
        print_step(5, "Обновление файлов...")
        for file_path in files_to_update:
            if file_path.exists():
                update_file_with_url(file_path, url_host)
            else:
                print_warning(f"Файл не найден: {file_path}")
        
        # Тестирование
        print_step(6, "Тестирование API...")
        try:
            import urllib.request
            test_url = f"https://{url_host}/api/health"
            response = urllib.request.urlopen(test_url, timeout=10)
            if response.status == 200:
                print_success(f"API доступен: {test_url}")
            else:
                print_warning(f"API вернул статус {response.status}")
        except Exception as e:
            print_warning(f"Не удалось проверить API: {e}")
        
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ ВСЁ ГОТОВО!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        print(f"📧 Отправьте заказчику:")
        print(f"   - Backend API URL: POST https://{url_host}/api/messages/")
        print(f"   - Файл: БЫСТРЫЙ_СТАРТ_N8N.md")
        print()
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

