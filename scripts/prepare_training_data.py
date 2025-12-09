#!/usr/bin/env python3
"""
Подготовка данных для обучения системы на основе реальных тикетов
"""
import json
import re
from collections import defaultdict
from typing import List, Dict, Tuple
from datetime import datetime

def extract_sender(message: str) -> Tuple[str, str]:
    """Извлечь отправителя и текст сообщения"""
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

def categorize_message(text: str) -> str:
    """
    Категоризация сообщения на основе паттернов
    Возвращает сценарий или None если не определен
    """
    text_lower = text.lower()
    
    # ABSENCE_REQUEST
    absence_patterns = [
        r"не будет.*присутствовать", r"отметьте.*отсутствие", r"не будет.*на занятии",
        r"не придет", r"отсутств", r"боле", r"болезн", r"не смогу.*занятие",
        r"авария.*линии", r"интернета нет", r"прошу.*отработк"
    ]
    if any(re.search(p, text_lower) for p in absence_patterns):
        return "ABSENCE_REQUEST"
    
    # SCHEDULE_CHANGE
    schedule_patterns = [
        r"перенос", r"перенести", r"смена.*времени", r"изменить.*время",
        r"другое время", r"другой тренер", r"когда.*урок", r"когда.*занятие",
        r"сегодня.*должен.*быть.*урок", r"расписание", r"не сможем.*заниматься"
    ]
    if any(re.search(p, text_lower) for p in schedule_patterns):
        return "SCHEDULE_CHANGE"
    
    # MISSING_TRAINER
    missing_trainer_patterns = [
        r"тренер.*нет", r"тренер.*не появился", r"тренер.*не пришел",
        r"урок.*не состоялся", r"занятие.*не было", r"прождали.*мин",
        r"уже.*но тренера нет"
    ]
    if any(re.search(p, text_lower) for p in missing_trainer_patterns):
        return "MISSING_TRAINER"
    
    # TECH_SUPPORT_BASIC
    tech_patterns = [
        r"не могу.*зайти", r"не работает", r"не открывается", r"ошибка",
        r"ссылка.*урок", r"не пришло.*сообщение", r"не получил.*ссылк",
        r"пароль.*не.*корректн", r"не удается.*зайти", r"платформ"
    ]
    if any(re.search(p, text_lower) for p in tech_patterns):
        return "TECH_SUPPORT_BASIC"
    
    # COMPLAINT
    complaint_patterns = [
        r"не предупредили", r"недоволен", r"плохо", r"что происходит",
        r"жалоб", r"претензи", r"некачественн", r"не понравилось"
    ]
    if any(re.search(p, text_lower) for p in complaint_patterns):
        return "COMPLAINT"
    
    # GREETING
    greeting_patterns = [
        r"^здравствуйте", r"^добрый день", r"^доброе утро", r"^добрый вечер",
        r"^привет"
    ]
    if any(re.search(p, text_lower) for p in greeting_patterns) and len(text) < 50:
        return "GREETING"
    
    # REFERRAL
    referral_patterns = [
        r"реферал", r"бонус.*друг", r"скидк", r"промокод", r"акци"
    ]
    if any(re.search(p, text_lower) for p in referral_patterns):
        return "REFERRAL"
    
    # REVIEW_BONUS
    review_patterns = [
        r"отзыв", r"бонус.*отзыв", r"урок.*отзыв"
    ]
    if any(re.search(p, text_lower) for p in review_patterns):
        return "REVIEW_BONUS"
    
    # CROSS_EXTENSION
    extension_patterns = [
        r"продлить", r"кросс", r"продление.*абонемент"
    ]
    if any(re.search(p, text_lower) for p in extension_patterns):
        return "CROSS_EXTENSION"
    
    # FAREWELL
    farewell_patterns = [
        r"спасибо", r"до свидания", r"все понятно", r"все ясно", r"все хорошо"
    ]
    if any(re.search(p, text_lower) for p in farewell_patterns) and len(text) < 50:
        return "FAREWELL"
    
    return "UNKNOWN"

def extract_training_samples(tickets: List[List[str]], max_samples: int = 10000) -> List[Dict]:
    """
    Извлечь примеры для обучения из тикетов
    """
    samples = []
    categories_count = defaultdict(int)
    
    for ticket_idx, ticket in enumerate(tickets):
        if len(ticket) == 0:
            continue
        
        # Найти первое сообщение клиента
        first_client_msg = None
        for msg in ticket:
            sender, text = extract_sender(msg)
            if sender == "client" and len(text.strip()) > 10:
                first_client_msg = text
                break
        
        if not first_client_msg:
            continue
        
        # Категоризировать
        category = categorize_message(first_client_msg)
        
        # Ограничить количество по категориям
        if categories_count[category] >= max_samples // 13:  # Равномерное распределение
            continue
        
        # Найти ответ админа (если есть)
        admin_response = None
        for msg in ticket:
            sender, text = extract_sender(msg)
            if sender in ["admin", "operator"] and len(text.strip()) > 10:
                admin_response = text
                break
        
        sample = {
            "message": first_client_msg,
            "scenario": category,
            "has_admin_response": admin_response is not None,
            "admin_response": admin_response,
            "ticket_length": len(ticket),
            "ticket_id": ticket_idx
        }
        
        samples.append(sample)
        categories_count[category] += 1
        
        if len(samples) >= max_samples:
            break
    
    return samples

def generate_few_shot_examples(samples: List[Dict]) -> Dict[str, List[str]]:
    """
    Генерация few-shot примеров для каждого сценария
    """
    examples_by_category = defaultdict(list)
    
    for sample in samples:
        category = sample["scenario"]
        if len(examples_by_category[category]) < 5:  # Максимум 5 примеров на категорию
            examples_by_category[category].append(sample["message"])
    
    return dict(examples_by_category)

def main():
    print("Загрузка тикетов...")
    with open("tickets.json", "r", encoding="utf-8") as f:
        tickets = json.load(f)
    
    print(f"Загружено {len(tickets):,} тикетов")
    print("Извлечение примеров для обучения...")
    
    # Извлечь примеры
    samples = extract_training_samples(tickets, max_samples=5000)
    
    print(f"Извлечено {len(samples)} примеров")
    
    # Статистика по категориям
    from collections import Counter
    category_counts = Counter(s["scenario"] for s in samples)
    print("\nРаспределение по категориям:")
    for category, count in category_counts.most_common():
        print(f"  {category}: {count}")
    
    # Сохранить датасет
    output_file = "training_dataset.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    
    print(f"\nДатасет сохранен в {output_file}")
    
    # Генерация few-shot примеров
    few_shot_examples = generate_few_shot_examples(samples)
    
    # Сохранить few-shot примеры
    few_shot_file = "few_shot_examples.json"
    with open(few_shot_file, "w", encoding="utf-8") as f:
        json.dump(few_shot_examples, f, ensure_ascii=False, indent=2)
    
    print(f"Few-shot примеры сохранены в {few_shot_file}")
    
    # Вывести примеры для промпта
    print("\n=== FEW-SHOT ПРИМЕРЫ ДЛЯ ПРОМПТА ===")
    for category, examples in sorted(few_shot_examples.items()):
        print(f"\n{category}:")
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example[:150]}...")

if __name__ == "__main__":
    main()







