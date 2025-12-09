"""
Message Response Service
Handles creation of bot responses based on processed messages
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Message, MessageType
from app.services.message_processing_service import ProcessedMessage
from app.services.reminder_service import ReminderService, ReminderType
from app.services.response_manager import ResponseManager

logger = logging.getLogger(__name__)


class MessageResponse:
    """Result of response creation"""
    def __init__(
        self,
        response_message: Message,
        response_text: str,
        scenario_response_message: Optional[Message] = None,
    ):
        self.response_message = response_message
        self.response_text = response_text
        self.scenario_response_message = scenario_response_message


class MessageResponseService:
    """Service for creating bot responses"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.response_manager = ResponseManager(session)
        self.reminder_service = ReminderService(session)

    async def create_response(
        self, processed_message: ProcessedMessage, client_id: str
    ) -> MessageResponse:
        """
        Create bot response based on processed message
        
        Returns:
            MessageResponse object with response message and text
        """
        scenario = processed_message.scenario
        requires_escalation = processed_message.requires_escalation
        is_first_message = processed_message.is_first_message
        scenario_msg = None  # Initialize to avoid NameError
        
        # Извлечь параметры из оригинального сообщения для персонализации
        original_content = processed_message.original_message.content
        extracted_params = self.response_manager.extract_params_from_message(
            original_content, scenario, client_id=client_id
        )
        
        # Добавить referral_link для REFERRAL сценария
        if scenario == "REFERRAL":
            extracted_params["referral_link"] = f"https://example.com/ref/{client_id}"

        # If this is the first message, analyze greeting and request time if needed
        # Согласно ТЗ: "Анализ приветствия (если нет упоминания диапазонов) - отправка сообщения - Запрос удобного времени и дней для занятий"
        greeting_text = None
        should_request_time = False
        
        if is_first_message:
            # Проверить, есть ли упоминание диапазонов/времени в сообщении
            message_lower = original_content.lower()
            time_keywords = [
                "время", "дни", "день", "неделя", "расписание", 
                "утро", "день", "вечер", "ночь",
                "понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье",
                "диапазон", "интервал", "часы", "час"
            ]
            has_time_mention = any(keyword in message_lower for keyword in time_keywords)
            
            if scenario == "GREETING" and not has_time_mention:
                # Если это просто приветствие без упоминания времени - запросить время
                should_request_time = True
                logger.info(f"First message is greeting without time mention, requesting time for {client_id}")
            elif scenario != "GREETING":
                # Для других сценариев - обычное приветствие
                greeting_text = await self.response_manager.get_response_text(
                    scenario="GREETING",
                    params={},
                )
                if greeting_text:
                    logger.debug(f"Got greeting text for first-time client {client_id} (will combine with main response)")

        # For escalated scenarios, send appropriate response
        # Special handling for TECH_SUPPORT_BASIC: send scenario template first (with screenshot request)
        # Other scenarios: send escalation notification
        if requires_escalation:
            # For TECH_SUPPORT_BASIC, send scenario template first (includes screenshot request)
            # This follows TZ requirement: first send instructions + screenshot request, then escalate
            if scenario == "TECH_SUPPORT_BASIC":
                # Send TECH_SUPPORT_BASIC template (includes screenshot request)
                response_msg, response_text = await self.response_manager.create_bot_response(
                    scenario="TECH_SUPPORT_BASIC",
                    client_id=client_id,
                    original_message_id=str(processed_message.original_message.id),
                    params=extracted_params,  # Использовать извлеченные параметры
                    message_type=MessageType.BOT_ESCALATED,  # Mark as escalated for operator notification
                )
                
                # If first message, combine greeting with tech support response
                # Но только если шаблон не начинается с приветствия
                if is_first_message and greeting_text:
                    response_starts_with_greeting = (
                        response_text.strip().startswith("Здравствуйте") or
                        response_text.strip().startswith("Привет") or
                        "Здравствуйте! 👋" in response_text[:50]
                    )
                    
                    if not response_starts_with_greeting:
                        # Combine greeting with tech support response
                        combined_text = f"{greeting_text}\n\n{response_text}"
                        response_msg.content = combined_text
                        response_text = combined_text
                        logger.info(f"✅ Combined greeting with TECH_SUPPORT_BASIC response for first-time client")
                    else:
                        logger.debug("TECH_SUPPORT_BASIC template already contains greeting, skipping separate greeting")
                
                logger.info(f"📤 Created TECH_SUPPORT_BASIC response (with screenshot request) for client {client_id}")
            else:
                # For other escalated scenarios, send scenario-specific response to client
                # This provides better UX - client gets specific information about their request
                # Scenarios that can be sent directly to client:
                # - SCHEDULE_CHANGE, COMPLAINT, MISSING_TRAINER, CROSS_EXTENSION, ABSENCE_REQUEST, REVIEW_BONUS
                # These templates are user-friendly and informative
                
                # Get scenario-specific response text (without creating DB record yet)
                scenario_response_text = await self.response_manager.get_response_text(
                    scenario=scenario,
                    params=extracted_params,  # Использовать извлеченные параметры
                )
                
                # If scenario template exists and is user-friendly, use it
                # Otherwise fall back to generic ESCALATED template
                if scenario_response_text:
                    # Create response with scenario-specific template
                    response_msg, response_text = await self.response_manager.create_bot_response(
                        scenario=scenario,
                        client_id=client_id,
                        original_message_id=str(processed_message.original_message.id),
                        params=extracted_params,  # Использовать извлеченные параметры
                        message_type=MessageType.BOT_ESCALATED,
                    )
                    logger.info(f"📤 Created scenario-specific escalation response ({scenario}) for client {client_id}")
                else:
                    # Fallback to generic ESCALATED template if scenario template not found
                    response_msg, response_text = await self.response_manager.create_bot_response(
                        scenario="ESCALATED",
                        client_id=client_id,
                        original_message_id=str(processed_message.original_message.id),
                        params={},
                        message_type=MessageType.BOT_ESCALATED,
                    )
                    logger.info(f"📤 Created generic escalation response for client {client_id} (scenario: {scenario})")
                
                # If first message, combine greeting with escalation message
                # Но только если шаблон не начинается с приветствия
                if is_first_message and greeting_text:
                    response_starts_with_greeting = (
                        response_text.strip().startswith("Здравствуйте") or
                        response_text.strip().startswith("Привет") or
                        "Здравствуйте! 👋" in response_text[:50]
                    )
                    
                    if not response_starts_with_greeting:
                        # Combine greeting with escalation message
                        combined_text = f"{greeting_text}\n\n{response_text}"
                        response_msg.content = combined_text
                        response_text = combined_text
                        logger.info(f"✅ Combined greeting with escalation response for first-time client")
                    else:
                        logger.debug(f"Escalation template for {scenario} already contains greeting, skipping separate greeting")
        else:
            # Normal auto response
            # Для LESSON_CANCELLATION - проверить, не возражает ли клиент
            if scenario == "LESSON_CANCELLATION":
                # Если клиент возражает против самостоятельной отмены - эскалировать
                message_lower = original_content.lower()
                objection_keywords = ["не могу", "не получается", "не работает", "помогите", "не знаю как", "не понимаю", "не умею"]
                if any(keyword in message_lower for keyword in objection_keywords):
                    # Клиент возражает - эскалировать оператору
                    requires_escalation = True
                    logger.info(f"Client {client_id} objects to self-cancellation, escalating to operator")
            
            # Для ABSENCE_REQUEST - попытаться отметить отсутствие в CRM
            if scenario == "ABSENCE_REQUEST":
                try:
                    from app.utils.crm_adapter import get_crm_adapter
                    from app.utils.entity_extractor import EntityExtractor
                    
                    crm_adapter = get_crm_adapter()
                    entity_extractor = EntityExtractor()
                    entities = entity_extractor.extract_entities(original_content)
                    
                    # Определить дату отсутствия
                    absence_date = datetime.now()  # По умолчанию сегодня
                    if entities.get("dates"):
                        date_str = entities["dates"][0].lower()
                        if date_str == "сегодня":
                            absence_date = datetime.now()
                        elif date_str == "завтра":
                            absence_date = datetime.now() + timedelta(days=1)
                        elif date_str == "вчера":
                            absence_date = datetime.now() - timedelta(days=1)
                    
                    # Определить причину
                    reason = extracted_params.get("reason", "Не указана")
                    message_lower = original_content.lower()
                    if "боле" in message_lower or "болезн" in message_lower:
                        reason = "Болезнь"
                    elif "интернет" in message_lower:
                        reason = "Проблемы с интернетом"
                    elif "авария" in message_lower:
                        reason = "Авария"
                    
                    # Попытаться отметить отсутствие в CRM
                    marked = await crm_adapter.mark_absence(
                        client_id=client_id,
                        date=absence_date,
                        reason=reason
                    )
                    
                    # Проверить, используется ли реальный CRM адаптер или Mock
                    from app.utils.crm_adapter import MockCRMAdapter
                    is_mock = isinstance(crm_adapter, MockCRMAdapter)
                    
                    if marked and not is_mock:
                        # Реальный CRM - отметка выполнена
                        logger.info(f"✅ Отмечено отсутствие в CRM для {client_id} на {absence_date.strftime('%d.%m.%Y')}")
                        # Обновить absence_note для указания успешного отметания
                        if extracted_params.get("child_name"):
                            extracted_params["absence_note"] = f"Отметил(а) отсутствие {extracted_params['child_name']} на {absence_date.strftime('%d.%m.%Y')}."
                        else:
                            extracted_params["absence_note"] = f"Отметил(а) отсутствие на {absence_date.strftime('%d.%m.%Y')}."
                        # Указать что отметка уже выполнена
                        extracted_params["crm_info"] = "Отметка отсутствия внесена в ваш личный кабинет."
                        extracted_params["crm_status"] = "marked"
                    else:
                        # MockCRMAdapter или ошибка - отметка будет выполнена оператором
                        logger.info(f"ℹ️ Отметка отсутствия будет выполнена оператором для {client_id}")
                        extracted_params["crm_info"] = "Отметка отсутствия будет внесена в ваш личный кабинет в течение 24 часов."
                        extracted_params["crm_status"] = "pending"
                except Exception as e:
                    logger.error(f"❌ Ошибка при отметке отсутствия в CRM: {e}")
                    # Продолжить с обычным ответом
            
            response_msg, response_text = await self.response_manager.create_bot_response(
                scenario=scenario,
                client_id=client_id,
                original_message_id=str(processed_message.original_message.id),
                params=extracted_params,  # Использовать извлеченные параметры
                message_type=MessageType.BOT_AUTO,
            )
            
            # If this is first message and scenario is not GREETING, combine greeting with response
            # Но только если шаблон сценария не начинается с приветствия (чтобы избежать дублирования)
            if is_first_message and greeting_text and scenario != "GREETING":
                # Проверить, начинается ли ответ сценария с приветствия
                response_starts_with_greeting = (
                    response_text.strip().startswith("Здравствуйте") or
                    response_text.strip().startswith("Привет") or
                    "Здравствуйте! 👋" in response_text[:50] or
                    "Приветствуем" in response_text[:50]
                )
                
                if response_starts_with_greeting:
                    # Шаблон уже содержит приветствие - не добавлять отдельное
                    logger.debug(f"Scenario {scenario} template already contains greeting, skipping separate greeting")
                else:
                    # Combine greeting text with scenario response text
                    combined_text = f"{greeting_text}\n\n{response_text}"
                    # Update response message content
                    response_msg.content = combined_text
                    response_text = combined_text
                    logger.info(f"✅ Combined greeting with {scenario} response for first-time client")
        
        # Если нужно запросить время (анализ приветствия согласно ТЗ)
        if should_request_time:
            time_request_text = await self.response_manager.get_response_text(
                scenario="GREETING_TIME_REQUEST",
                params={},
            )
            if time_request_text:
                # Создать отдельное сообщение с запросом времени
                time_request_msg, _ = await self.response_manager.create_bot_response(
                    scenario="GREETING_TIME_REQUEST",
                    client_id=client_id,
                    original_message_id=str(processed_message.original_message.id),
                    params={},
                    message_type=MessageType.BOT_AUTO,
                )
                # Использовать это сообщение как основное
                response_msg = time_request_msg
                response_text = time_request_msg.content
                logger.info(f"✅ Sent time request for first-time client {client_id}")

        if not response_msg:
            logger.error("❌ Failed to create response, using fallback")
            response_msg, response_text = await self.response_manager.create_fallback_response(
                client_id, reason="response_creation_error"
            )

        if not response_msg:
            raise RuntimeError("Failed to create bot response after fallback")

        logger.info(f"✅ Created response: {response_msg.id}")

        return MessageResponse(
            response_message=response_msg,
            response_text=response_text,
            scenario_response_message=scenario_msg if requires_escalation else None,
        )

    async def create_reminders(
        self,
        client_id: str,
        message_id: str,
        requires_escalation: bool,
        scenario: str,
    ) -> None:
        """
        Create reminders for client if needed
        
        Reminders are not created for:
        - Escalated messages
        - FAREWELL scenario
        - UNKNOWN scenario
        """
        if requires_escalation or scenario in ["FAREWELL", "UNKNOWN"]:
            logger.debug(f"Skipping reminders for scenario {scenario}")
            return

        await self.reminder_service.create_reminder(
            client_id=client_id,
            message_id=message_id,
            reminder_type=ReminderType.REMINDER_15MIN,
        )

        await self.reminder_service.create_reminder(
            client_id=client_id,
            message_id=message_id,
            reminder_type=ReminderType.REMINDER_30MIN,
        )
        
        # Add reminder for next day (per TZ requirement)
        await self.reminder_service.create_reminder(
            client_id=client_id,
            message_id=message_id,
            reminder_type=ReminderType.REMINDER_1DAY,
        )

        logger.debug(f"Created reminders (15min, 30min, 1day) for message {message_id}")

    async def cancel_pending_reminders(
        self, client_id: str, after_message_id: str
    ) -> int:
        """
        Cancel pending reminders for messages created after this one
        
        Returns:
            Number of cancelled reminders
        """
        cancelled = await self.reminder_service.cancel_client_reminders(
            client_id=client_id,
            after_message_id=after_message_id,
        )
        if cancelled > 0:
            logger.debug(
                f"Cancelled {cancelled} pending reminders for {client_id}"
            )
        return cancelled

    async def finalize_message_processing(
        self, processed_message: ProcessedMessage
    ) -> None:
        """
        Finalize message processing:
        - Mark message as processed
        - Create reminders
        - Cancel old reminders
        """
        # Mark original as processed
        processed_message.original_message.is_processed = True

        # Create reminders if needed
        await self.create_reminders(
            client_id=processed_message.original_message.client_id,
            message_id=str(processed_message.original_message.id),
            requires_escalation=processed_message.requires_escalation,
            scenario=processed_message.scenario,
        )

        # Cancel pending reminders for messages created after this one
        await self.cancel_pending_reminders(
            client_id=processed_message.original_message.client_id,
            after_message_id=str(processed_message.original_message.id),
        )

