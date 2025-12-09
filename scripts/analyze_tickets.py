#!/usr/bin/env python3
"""
Анализ реальных тикетов для обучения системы
"""
import json
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
from datetime import datetime

def load_tickets(filepath: str) -> List[List[str]]:
    """Загрузить тикеты из JSON файла"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_sender(message: str) -> Tuple[str, str]:
    """
    Извлечь отправителя и текст сообщения
    
    Возвращает: (sender_type, message_text)
    sender_type: 'client', 'admin', 'operator', 'unknown'
    """
    message = message.strip()
    
    if message.startswith("клиент -"):
        return ("client", message.replace("клиент -", "", 1).strip())
    elif message.startswith("админ -"):
        return ("admin", message.replace("админ -", "", 1).strip())
    elif message.startswith("оператор -"):
        return ("operator", message.replace("оператор -", "", 1).strip())
    elif message.startswith("менеджер -"):
        return ("operator", message.replace("менеджер -", "", 1).strip())
    else:
        return ("unknown", message)

def analyze_ticket_structure(tickets: List[List[str]]) -> Dict:
    """Анализ структуры тикетов"""
    stats = {
        "total_tickets": len(tickets),
        "total_messages": sum(len(ticket) for ticket in tickets),
        "tickets_by_length": Counter(),
        "messages_by_sender": Counter(),
        "empty_tickets": 0,
    }
    
    for ticket in tickets:
        if len(ticket) == 0:
            stats["empty_tickets"] += 1
            continue
            
        stats["tickets_by_length"][len(ticket)] += 1
        
        for msg in ticket:
            sender, _ = extract_sender(msg)
            stats["messages_by_sender"][sender] += 1
    
    return stats

def categorize_client_messages(messages: List[str]) -> Dict[str, List[str]]:
    """
    Категоризация сообщений клиентов по типам запросов
    """
    categories = defaultdict(list)
    
    # Паттерны для категоризации
    patterns = {
        "greeting": [
            r"здравств", r"привет", r"добр", r"доброе утро", r"добрый день", r"добрый вечер"
        ],
        "absence_request": [
            r"не будет", r"не придет", r"отсутств", r"пропуск", r"боле", r"болезн",
            r"не смогу", r"не смогут", r"отметьте отсутствие", r"отсутствие"
        ],
        "schedule_change": [
            r"перенос", r"перенести", r"смена", r"изменить", r"другое время",
            r"другой тренер", r"расписание", r"когда занятие", r"когда урок"
        ],
        "technical_support": [
            r"не работает", r"не могу", r"не заходит", r"ошибка", r"проблем",
            r"ссылка", r"не пришло", r"не получил", r"не открывается"
        ],
        "complaint": [
            r"жалоб", r"недоволен", r"плохо", r"плох", r"не устраивает",
            r"претензи", r"некачественн", r"не понравилось"
        ],
        "referral": [
            r"реферал", r"бонус", r"скидк", r"промокод", r"акци"
        ],
        "review_bonus": [
            r"отзыв", r"бонус за отзыв", r"урок за отзыв"
        ],
        "farewell": [
            r"спасибо", r"до свидания", r"все понятно", r"все ясно", r"все хорошо"
        ],
        "missing_trainer": [
            r"тренер не пришел", r"тренер не появился", r"урок не состоялся",
            r"занятие не было", r"не было урока"
        ],
        "cross_extension": [
            r"продлить", r"кросс", r"продление", r"абонемент"
        ],
    }
    
    for msg in messages:
        sender, text = extract_sender(msg)
        if sender != "client":
            continue
            
        text_lower = text.lower()
        categorized = False
        
        for category, category_patterns in patterns.items():
            for pattern in category_patterns:
                if re.search(pattern, text_lower):
                    categories[category].append(text)
                    categorized = True
                    break
            if categorized:
                break
        
        if not categorized:
            categories["unknown"].append(text)
    
    return dict(categories)

def analyze_client_requests(tickets: List[List[str]]) -> Dict:
    """Анализ запросов клиентов"""
    client_messages = []
    
    for ticket in tickets:
        for msg in ticket:
            sender, text = extract_sender(msg)
            if sender == "client":
                client_messages.append(text)
    
    # Категоризация
    categories = categorize_client_messages(client_messages)
    
    # Статистика по категориям
    category_stats = {
        category: {
            "count": len(messages),
            "percentage": len(messages) / len(client_messages) * 100 if client_messages else 0,
            "sample_messages": messages[:5]  # Первые 5 примеров
        }
        for category, messages in categories.items()
    }
    
    return {
        "total_client_messages": len(client_messages),
        "categories": category_stats,
        "all_client_messages": client_messages[:100]  # Первые 100 для анализа
    }

def analyze_admin_responses(tickets: List[List[str]]) -> Dict:
    """Анализ ответов админов/операторов"""
    admin_messages = []
    response_patterns = Counter()
    
    for ticket in tickets:
        admin_msgs_in_ticket = []
        for msg in ticket:
            sender, text = extract_sender(msg)
            if sender in ["admin", "operator"]:
                admin_msgs_in_ticket.append(text)
        
        if admin_msgs_in_ticket:
            admin_messages.extend(admin_msgs_in_ticket)
            
            # Анализ паттернов ответов
            first_admin_msg = admin_msgs_in_ticket[0].lower()
            if "здравств" in first_admin_msg or "добр" in first_admin_msg:
                response_patterns["greeting"] += 1
            if "отметил" in first_admin_msg or "отмечено" in first_admin_msg:
                response_patterns["confirmation"] += 1
            if "ссылка" in first_admin_msg or "http" in first_admin_msg:
                response_patterns["link_provided"] += 1
    
    return {
        "total_admin_messages": len(admin_messages),
        "response_patterns": dict(response_patterns),
        "sample_responses": admin_messages[:50]
    }

def find_common_phrases(messages: List[str], min_length: int = 3) -> List[Tuple[str, int]]:
    """Найти наиболее частые фразы в сообщениях"""
    phrase_counter = Counter()
    
    for msg in messages:
        # Разбить на слова и найти фразы
        words = re.findall(r'\b[а-яё]{3,}\b', msg.lower())
        for i in range(len(words) - min_length + 1):
            phrase = " ".join(words[i:i+min_length])
            phrase_counter[phrase] += 1
    
    return phrase_counter.most_common(20)

def generate_analysis_report(tickets: List[List[str]]) -> str:
    """Генерация отчета анализа"""
    report = []
    report.append("=" * 80)
    report.append("АНАЛИЗ РЕАЛЬНЫХ ТИКЕТОВ ДЛЯ ОБУЧЕНИЯ СИСТЕМЫ")
    report.append("=" * 80)
    report.append(f"\nДата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Структура тикетов
    structure_stats = analyze_ticket_structure(tickets)
    report.append("=== СТРУКТУРА ДАННЫХ ===")
    report.append(f"Всего тикетов: {structure_stats['total_tickets']:,}")
    report.append(f"Всего сообщений: {structure_stats['total_messages']:,}")
    report.append(f"Среднее сообщений на тикет: {structure_stats['total_messages'] / structure_stats['total_tickets']:.2f}")
    report.append(f"Пустых тикетов: {structure_stats['empty_tickets']}")
    report.append(f"\nРаспределение по длине:")
    for length, count in sorted(structure_stats['tickets_by_length'].items())[:10]:
        report.append(f"  {length} сообщений: {count:,} тикетов")
    
    report.append(f"\nРаспределение сообщений по отправителям:")
    for sender, count in structure_stats['messages_by_sender'].most_common():
        report.append(f"  {sender}: {count:,}")
    
    # Анализ запросов клиентов
    client_analysis = analyze_client_requests(tickets)
    report.append("\n\n=== АНАЛИЗ ЗАПРОСОВ КЛИЕНТОВ ===")
    report.append(f"Всего сообщений от клиентов: {client_analysis['total_client_messages']:,}")
    report.append("\nКатегоризация запросов:")
    for category, stats in sorted(client_analysis['categories'].items(), 
                                  key=lambda x: x[1]['count'], reverse=True):
        report.append(f"\n  {category.upper()}:")
        report.append(f"    Количество: {stats['count']:,} ({stats['percentage']:.1f}%)")
        report.append(f"    Примеры:")
        for i, sample in enumerate(stats['sample_messages'][:3], 1):
            preview = sample[:150] + "..." if len(sample) > 150 else sample
            report.append(f"      {i}. {preview}")
    
    # Анализ ответов админов
    admin_analysis = analyze_admin_responses(tickets)
    report.append("\n\n=== АНАЛИЗ ОТВЕТОВ АДМИНОВ/ОПЕРАТОРОВ ===")
    report.append(f"Всего сообщений от админов: {admin_analysis['total_admin_messages']:,}")
    report.append("\nПаттерны ответов:")
    for pattern, count in admin_analysis['response_patterns'].items():
        report.append(f"  {pattern}: {count:,}")
    
    # Частые фразы
    client_messages = [extract_sender(msg)[1] for ticket in tickets for msg in ticket 
                      if extract_sender(msg)[0] == "client"]
    common_phrases = find_common_phrases(client_messages[:1000])
    report.append("\n\n=== ЧАСТЫЕ ФРАЗЫ В ЗАПРОСАХ КЛИЕНТОВ ===")
    for phrase, count in common_phrases:
        report.append(f"  '{phrase}': {count} раз")
    
    report.append("\n" + "=" * 80)
    
    return "\n".join(report)

if __name__ == "__main__":
    print("Загрузка тикетов...")
    tickets = load_tickets("tickets.json")
    
    print("Анализ данных...")
    report = generate_analysis_report(tickets)
    
    # Сохранить отчет
    with open("tickets_analysis_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\nОтчет сохранен в tickets_analysis_report.txt")
    print("\n" + "=" * 80)
    print(report[:2000])  # Показать первые 2000 символов
    print("\n... (полный отчет в файле)")







