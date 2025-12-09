"""
Tests for classification on real production data
"""
import pytest
from app.services.ai_classifier import AIClassifier
from app.services.text_processor import TextProcessor


@pytest.mark.asyncio
async def test_classification_on_real_samples():
    """Test classification on real samples from tickets.json"""
    
    classifier = AIClassifier()
    text_processor = TextProcessor()
    
    # Real samples from production data
    test_cases = [
        {
            "text": "Сегодня Владочка Веряскина не будет присутствовать на занятии. У нас проблемы с интернетом. Отметьте пожалуйста отсутствие ее",
            "expected_scenario": "ABSENCE_REQUEST",
            "min_confidence": 0.8,
        },
        {
            "text": "здравствуйте, а у нас сегодня должен быть урок?",
            "expected_scenario": "SCHEDULE_CHANGE",
            "min_confidence": 0.75,
        },
        {
            "text": "не удается зайти на платформу для выполнения дз, пишет пароль не корректный",
            "expected_scenario": "TECH_SUPPORT_BASIC",
            "min_confidence": 0.8,
        },
        {
            "text": "У нас урок должен начаться в 10:15 по мск , а уже 10:25 , но тренера нет",
            "expected_scenario": "MISSING_TRAINER",
            "min_confidence": 0.85,
        },
        {
            "text": "Во-первых нас не предупредили,что наш учитель уходит это для нас очень важно...теперь ещё и день не наш...что происходит????",
            "expected_scenario": "COMPLAINT",
            "min_confidence": 0.8,
        },
        {
            "text": "А можно продлить занятия?",
            "expected_scenario": "CROSS_EXTENSION",
            "min_confidence": 0.8,
        },
        {
            "text": "Добрый день! Есть на 2 месяца ?",
            "expected_scenario": "GREETING",
            "min_confidence": 0.7,
        },
        {
            "text": "Спасибо большое",
            "expected_scenario": "FAREWELL",
            "min_confidence": 0.7,
        },
    ]
    
    results = []
    for i, test_case in enumerate(test_cases):
        # Process text
        processed_text = text_processor.process(test_case["text"])
        
        # Classify
        result = await classifier.classify(processed_text, client_id=f"test_{i}")
        
        results.append({
            "original": test_case["text"],
            "processed": processed_text,
            "expected": test_case["expected_scenario"],
            "actual": result.get("scenario"),
            "confidence": result.get("confidence", 0),
            "success": result.get("scenario") == test_case["expected_scenario"] 
                      and result.get("confidence", 0) >= test_case["min_confidence"],
        })
    
    # Print results
    print("\n=== Classification Test Results ===")
    success_count = sum(1 for r in results if r["success"])
    print(f"Success rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"\n{status} Test: {r['original'][:60]}...")
        print(f"   Expected: {r['expected']}, Got: {r['actual']} (confidence: {r['confidence']:.2f})")
    
    # Assert minimum success rate
    assert success_count >= len(results) * 0.7, f"Success rate {success_count/len(results)*100:.1f}% below 70%"


@pytest.mark.asyncio
async def test_text_processor_on_real_data():
    """Test text processor on real production data"""
    
    processor = TextProcessor()
    
    test_cases = [
        {
            "input": "  Сегодня   Владочка    Веряскина   не   будет   ",
            "should_clean": True,
        },
        {
            "input": "отправлено мобильной яндекс почты пересылаемое сообщение",
            "should_remove_artifacts": True,
        },
        {
            "input": "не могу заити",
            "should_fix_typo": True,
            "expected_contains": "зайти",
        },
    ]
    
    for test_case in test_cases:
        result = processor.process(test_case["input"])
        
        if test_case.get("should_clean"):
            assert "  " not in result, "Multiple spaces not cleaned"
        
        if test_case.get("should_remove_artifacts"):
            assert "яндекс почты" not in result.lower(), "Email artifacts not removed"
        
        if test_case.get("should_fix_typo") and test_case.get("expected_contains"):
            assert test_case["expected_contains"] in result.lower(), f"Typo not fixed: {test_case['input']}"


@pytest.mark.asyncio
async def test_emotion_analysis():
    """Test emotion analysis on real complaint samples"""
    
    from app.services.escalation_manager import EscalationManager
    from app.database import async_session_maker
    
    async with async_session_maker() as session:
        manager = EscalationManager(session)
        
        test_cases = [
            {
                "text": "что происходит????",
                "should_be_negative": True,
            },
            {
                "text": "Во-первых нас не предупредили,что наш учитель уходит это для нас очень важно...теперь ещё и день не наш...что происходит????",
                "should_be_negative": True,
            },
            {
                "text": "Спасибо большое",
                "should_be_negative": False,
            },
        ]
        
        for test_case in test_cases:
            emotion = manager.analyze_emotion(test_case["text"])
            
            if test_case["should_be_negative"]:
                assert emotion["is_negative"], f"Should be negative: {test_case['text']}"
                assert emotion["score"] > 0.5, f"Emotion score too low: {emotion['score']}"
            else:
                assert not emotion["is_negative"], f"Should not be negative: {test_case['text']}"


@pytest.mark.asyncio
async def test_entity_extraction():
    """Test entity extraction on real data"""
    
    from app.utils.entity_extractor import EntityExtractor
    
    extractor = EntityExtractor()
    
    test_cases = [
        {
            "text": "Сегодня Владочка Веряскина не будет присутствовать на занятии",
            "should_have_name": True,
            "expected_name": "Владочка",  # Может быть извлечено как отдельные имена
        },
        {
            "text": "У нас урок должен начаться в 10:15 по мск , а уже 10:25",
            "should_have_time": True,
        },
        {
            "text": "26 марта",
            "should_have_date": True,
        },
    ]
    
    for test_case in test_cases:
        entities = extractor.extract_entities(test_case["text"])
        
        if test_case.get("should_have_name"):
            assert entities["has_name"], f"Should extract name from: {test_case['text']}"
            if test_case.get("expected_name"):
                # Проверить, что ожидаемое имя присутствует в любом из извлеченных имен
                found = any(test_case["expected_name"] in name for name in entities["child_names"])
                assert found, \
                    f"Expected name '{test_case['expected_name']}' not found in {entities['child_names']}"
        
        if test_case.get("should_have_time"):
            assert entities["has_time"], f"Should extract time from: {test_case['text']}"
        
        if test_case.get("should_have_date"):
            assert entities["has_date"], f"Should extract date from: {test_case['text']}"

