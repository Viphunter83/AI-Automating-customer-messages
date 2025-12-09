"""
Simple Named Entity Recognition for extracting names and context from messages
Based on patterns from real production data
"""
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract named entities (names, dates, times) from messages"""
    
    # Паттерны для извлечения имен детей (из реальных данных)
    # Имена обычно идут с заглавной буквы, часто в формате "Имя Фамилия"
    NAME_PATTERNS = [
        r"\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b",  # Имя Фамилия
        r"\b[А-ЯЁ][а-яё]{2,}\b",  # Одно слово с заглавной (имя)
    ]
    
    # Паттерны для дат
    DATE_PATTERNS = [
        r"\b(сегодня|завтра|вчера|послезавтра)\b",
        r"\b\d{1,2}\s+(январ|феврал|март|апрел|май|июн|июл|август|сентябр|октябр|ноябр|декабр)",
        r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b",  # ДД.ММ.ГГГГ
        r"\b\d{1,2}\s+марта|\d{1,2}\s+апреля",  # "26 марта"
    ]
    
    # Паттерны для времени
    TIME_PATTERNS = [
        r"\b\d{1,2}:\d{2}\b",  # ЧЧ:ММ
        r"\b\d{1,2}\s+час[аов]?\b",  # "10 часов"
        r"\b(утр|день|вечер|ночь)\b",
    ]
    
    # Паттерны для предметов/направлений (из реальных данных)
    SUBJECT_PATTERNS = [
        r"\b(математик|скорочтени|ментальн|логопеди|развити[ея] речи)\b",
        r"\b(английск|русск|литератур)\b",
    ]
    
    def extract_entities(self, text: str) -> Dict[str, any]:
        """
        Extract entities from text
        
        Returns:
            {
                "child_names": List[str],
                "dates": List[str],
                "times": List[str],
                "subjects": List[str],
                "has_name": bool,
                "has_date": bool,
                "has_time": bool,
            }
        """
        if not text or len(text.strip()) < 3:
            return self._empty_result()
        
        text_original = text  # Сохранить оригинал для извлечения имен
        text_lower = text.lower()
        
        # Извлечение имен
        child_names = self._extract_names(text_original)
        
        # Извлечение дат
        dates = self._extract_dates(text_lower)
        
        # Извлечение времени
        times = self._extract_times(text_lower)
        
        # Извлечение предметов
        subjects = self._extract_subjects(text_lower)
        
        return {
            "child_names": child_names,
            "dates": dates,
            "times": times,
            "subjects": subjects,
            "has_name": len(child_names) > 0,
            "has_date": len(dates) > 0,
            "has_time": len(times) > 0,
        }
    
    def _extract_names(self, text: str) -> List[str]:
        """Extract child names from text"""
        names = []
        
        # Исключить общие слова, которые могут быть приняты за имена
        exclude_words = {
            # Приветствия
            "привет", "приветствую", "здравствуйте", "здравствуй", "добрый", "доброе", "добрый день", "добрый вечер",
            "доброе утро", "добрый вечер", "доброй ночи",
            # Вежливые слова
            "спасибо", "пожалуйста", "можно", "подскажите", "помогите", "прошу",
            # Временные слова
            "сегодня", "завтра", "вчера", "послезавтра",
            # Существительные (не имена)
            "тренер", "тренера", "тренеру", "занятие", "занятия", "урок", "урока", "уроков",
            "платформа", "платформу", "ссылка", "ссылки", "пароль", "пароля",
            "ребенок", "ребенка", "ребенку", "дети", "детей",
            # Глаголы
            "отметьте", "отметил", "отметила", "отметить", "отметить", "нужно", "нужен", "нужна",
            "будет", "буду", "будешь", "будем", "будете", "будут",
            # Предлоги и частицы
            "не", "на", "в", "с", "по", "для", "от", "до", "из", "к", "о", "об", "про",
            # Местоимения
            "нас", "нам", "вас", "вам", "их", "его", "ее", "мне", "мне", "тебе", "ему", "ей",
            "я", "ты", "он", "она", "мы", "вы", "они",
            # Другие частые слова
            "знаю", "знает", "знаете", "делать", "делаю", "делает", "хочу", "хотят",
            "пропустить", "пропущу", "пропустит", "пропуск", "пропуска",
        }
        
        # Разделить текст на предложения для лучшего контекста
        sentences = re.split(r'[.!?]\s+', text)
        first_sentence = sentences[0] if sentences else ""
        
        for pattern in self.NAME_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                # Проверить, не является ли это исключенным словом
                words = match.split()
                valid_name = True
                
                for word in words:
                    word_lower = word.lower()
                    # Проверить каждое слово в фразе
                    if word_lower in exclude_words:
                        valid_name = False
                        break
                    # Исключить слова, которые явно не имена (глаголы, предлоги)
                    if len(word) < 3:
                        valid_name = False
                        break
                
                # Дополнительная проверка: если слово в начале первого предложения и это приветствие - исключить
                if valid_name and first_sentence:
                    match_lower = match.lower()
                    # Проверить, не является ли это первым словом в предложении (вероятно приветствие)
                    first_words = first_sentence.split()[:2]  # Первые 1-2 слова
                    if any(match_lower.startswith(w.lower()) or w.lower() in match_lower for w in first_words):
                        # Если это короткое слово в начале - вероятно не имя
                        if len(match.replace(" ", "")) < 6:
                            # Проверить, не является ли это приветствием
                            if match_lower in exclude_words or any(w.lower() in exclude_words for w in words):
                                valid_name = False
                
                # Исключить слишком короткие "имена" (менее 4 символов)
                # Исключить фразы где все слова короткие (вероятно не имя)
                if valid_name and len(match.replace(" ", "")) >= 4:
                    # Дополнительная проверка: имя должно содержать хотя бы одно слово >= 4 символов
                    has_long_word = any(len(w) >= 4 for w in words)
                    if has_long_word:
                        # Убрать дубликаты и добавить
                        if match not in names:
                            names.append(match)
        
        # Ограничить количество (обычно в сообщении 1-2 имени)
        return names[:3]
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text"""
        dates = []
        
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = " ".join(match)
                if match not in dates:
                    dates.append(match)
        
        return dates[:5]  # Максимум 5 дат
    
    def _extract_times(self, text: str) -> List[str]:
        """Extract times from text"""
        times = []
        
        for pattern in self.TIME_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = " ".join(match)
                if match not in times:
                    times.append(match)
        
        return times[:5]  # Максимум 5 времен
    
    def _extract_subjects(self, text: str) -> List[str]:
        """Extract subjects/courses from text"""
        subjects = []
        
        for pattern in self.SUBJECT_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = " ".join(match)
                if match not in subjects:
                    subjects.append(match)
        
        return subjects[:3]  # Максимум 3 предмета
    
    def _empty_result(self) -> Dict[str, any]:
        """Return empty result structure"""
        return {
            "child_names": [],
            "dates": [],
            "times": [],
            "subjects": [],
            "has_name": False,
            "has_date": False,
            "has_time": False,
        }
    
    def get_first_child_name(self, text: str) -> Optional[str]:
        """Get first child name from text, if any"""
        entities = self.extract_entities(text)
        if entities["child_names"]:
            return entities["child_names"][0]
        return None

