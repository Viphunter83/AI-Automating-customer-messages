"""
Script to create test data for the AI Customer Support system
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import select
from app.database import async_session_maker
from app.models.database import (
    Message, MessageType, Classification, ScenarioType,
    ResponseTemplate, OperatorFeedback, Keyword
)
from app.services.response_manager import ResponseManager

async def create_test_data():
    """Create comprehensive test data"""
    print("=" * 70)
    print("CREATING TEST DATA")
    print("=" * 70)
    
    async with async_session_maker() as session:
        # 1. Initialize default templates
        print("\n1️⃣  Initializing response templates...")
        manager = ResponseManager(session)
        await manager.initialize_default_templates()
        await session.commit()
        print("   ✅ Templates initialized")
        
        # 2. Create test messages and classifications
        print("\n2️⃣  Creating test messages and classifications...")
        
        test_cases = [
            {
                "client_id": "client_001",
                "content": "Привет! Как дела?",
                "scenario": "GREETING",
                "confidence": 0.95,
                "reasoning": "Клиент приветствует и интересуется делами"
            },
            {
                "client_id": "client_001",
                "content": "Как работает реферальная программа?",
                "scenario": "REFERRAL",
                "confidence": 0.98,
                "reasoning": "Прямой вопрос о реферальной программе"
            },
            {
                "client_id": "client_002",
                "content": "Не могу зайти в кабинет, ошибка 404",
                "scenario": "TECH_SUPPORT_BASIC",
                "confidence": 0.92,
                "reasoning": "Проблема доступа в кабинет"
            },
            {
                "client_id": "client_002",
                "content": "Здравствуйте!",
                "scenario": "GREETING",
                "confidence": 0.97,
                "reasoning": "Простое приветствие"
            },
            {
                "client_id": "client_003",
                "content": "Какой сегодня день недели?",
                "scenario": "UNKNOWN",
                "confidence": 0.75,
                "reasoning": "Вопрос не относится к теме школы"
            },
            {
                "client_id": "client_003",
                "content": "Хочу узнать про бонусы за рефералов",
                "scenario": "REFERRAL",
                "confidence": 0.96,
                "reasoning": "Вопрос о бонусах реферальной программы"
            },
        ]
        
        messages_created = []
        classifications_created = []
        
        for i, test_case in enumerate(test_cases):
            # Create message
            message = Message(
                id=uuid4(),
                client_id=test_case["client_id"],
                content=test_case["content"],
                message_type=MessageType.USER,
                is_processed=True,
                created_at=datetime.utcnow() - timedelta(hours=24-i)
            )
            session.add(message)
            await session.flush()
            messages_created.append(message)
            
            # Create classification
            classification = Classification(
                id=uuid4(),
                message_id=message.id,
                detected_scenario=ScenarioType[test_case["scenario"]],
                confidence=test_case["confidence"],
                ai_model="gpt-4o-mini",
                reasoning=test_case["reasoning"],
                created_at=message.created_at
            )
            session.add(classification)
            await session.flush()
            classifications_created.append(classification)
            
            # Create bot response
            response_msg, response_text = await manager.create_bot_response(
                scenario=test_case["scenario"],
                client_id=test_case["client_id"],
                original_message_id=str(message.id),
                params={"referral_link": f"https://example.com/ref/{test_case['client_id']}"},
                message_type=MessageType.BOT_AUTO if test_case["scenario"] != "UNKNOWN" else MessageType.BOT_ESCALATED
            )
            if response_msg:
                response_msg.created_at = message.created_at + timedelta(seconds=5)
                await session.flush()
        
        await session.commit()
        print(f"   ✅ Created {len(messages_created)} messages and {len(classifications_created)} classifications")
        
        # 3. Create operator feedback
        print("\n3️⃣  Creating operator feedback...")
        
        feedback_cases = [
            {
                "message_id": messages_created[0].id,
                "classification_id": classifications_created[0].id,
                "operator_id": "operator_001",
                "feedback_type": "correct",
                "suggested_scenario": None,
                "comment": "Правильно классифицировано"
            },
            {
                "message_id": messages_created[1].id,
                "classification_id": classifications_created[1].id,
                "operator_id": "operator_001",
                "feedback_type": "correct",
                "suggested_scenario": None,
                "comment": None
            },
            {
                "message_id": messages_created[4].id,
                "classification_id": classifications_created[4].id,
                "operator_id": "operator_002",
                "feedback_type": "incorrect",
                "suggested_scenario": ScenarioType.GREETING,
                "comment": "Должно быть приветствие, а не UNKNOWN"
            },
        ]
        
        feedbacks_created = []
        for feedback_case in feedback_cases:
            feedback = OperatorFeedback(
                id=uuid4(),
                message_id=feedback_case["message_id"],
                classification_id=feedback_case["classification_id"],
                operator_id=feedback_case["operator_id"],
                feedback_type=feedback_case["feedback_type"],
                suggested_scenario=feedback_case["suggested_scenario"],
                comment=feedback_case["comment"],
                created_at=datetime.utcnow() - timedelta(hours=12)
            )
            session.add(feedback)
            feedbacks_created.append(feedback)
        
        await session.commit()
        print(f"   ✅ Created {len(feedbacks_created)} feedback entries")
        
        # 4. Create keywords
        print("\n4️⃣  Creating keywords...")
        
        keyword_cases = [
            {"scenario": ScenarioType.GREETING, "keyword": "привет", "priority": 10},
            {"scenario": ScenarioType.GREETING, "keyword": "здравствуйте", "priority": 10},
            {"scenario": ScenarioType.GREETING, "keyword": "добрый день", "priority": 9},
            {"scenario": ScenarioType.REFERRAL, "keyword": "реферал", "priority": 10},
            {"scenario": ScenarioType.REFERRAL, "keyword": "бонус", "priority": 9},
            {"scenario": ScenarioType.REFERRAL, "keyword": "скидка", "priority": 8},
            {"scenario": ScenarioType.TECH_SUPPORT_BASIC, "keyword": "ошибка", "priority": 10},
            {"scenario": ScenarioType.TECH_SUPPORT_BASIC, "keyword": "не могу зайти", "priority": 9},
            {"scenario": ScenarioType.TECH_SUPPORT_BASIC, "keyword": "кабинет", "priority": 8},
        ]
        
        keywords_created = []
        for kw_case in keyword_cases:
            keyword = Keyword(
                id=uuid4(),
                scenario_name=kw_case["scenario"],
                keyword=kw_case["keyword"],
                priority=kw_case["priority"]
            )
            session.add(keyword)
            keywords_created.append(keyword)
        
        await session.commit()
        print(f"   ✅ Created {len(keywords_created)} keywords")
        
        # 5. Summary
        print("\n" + "=" * 70)
        print("✅ TEST DATA CREATED SUCCESSFULLY")
        print("=" * 70)
        print(f"\n📊 Summary:")
        print(f"   Messages: {len(messages_created)}")
        print(f"   Classifications: {len(classifications_created)}")
        print(f"   Feedback entries: {len(feedbacks_created)}")
        print(f"   Keywords: {len(keywords_created)}")
        print(f"   Templates: 4 (GREETING, REFERRAL, TECH_SUPPORT_BASIC, UNKNOWN)")
        print(f"\n👥 Test clients:")
        print(f"   - client_001 (2 messages)")
        print(f"   - client_002 (2 messages)")
        print(f"   - client_003 (2 messages)")
        print(f"\n👨‍💼 Test operators:")
        print(f"   - operator_001 (2 feedbacks)")
        print(f"   - operator_002 (1 feedback)")
        print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(create_test_data())

