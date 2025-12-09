import logging
import uuid
from typing import Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Message, MessageType, ResponseTemplate, ScenarioType
from app.utils.cache import get_cache
from app.utils.prompts import RESPONSE_TEMPLATES
from app.utils.entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)


class ResponseManager:
    """Manage response templates and selection"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.entity_extractor = EntityExtractor()

    async def initialize_default_templates(self) -> None:
        """
        Initialize default response templates in database
        Called once during app startup
        """
        logger.info("Initializing default response templates...")

        for scenario_name, template_data in RESPONSE_TEMPLATES.items():
            try:
                # Check if scenario exists in ScenarioType enum
                if scenario_name not in ScenarioType.__members__:
                    logger.warning(f"Scenario {scenario_name} not found in ScenarioType enum, skipping")
                    continue

                # Check if already exists
                result = await self.session.execute(
                    select(ResponseTemplate).where(
                        ResponseTemplate.scenario_name == ScenarioType[scenario_name]
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    logger.debug(f"Template {scenario_name} already exists, skipping")
                    continue

                # Create new template
                template = ResponseTemplate(
                    id=uuid.uuid4(),
                    scenario_name=ScenarioType[scenario_name],
                    template_text=template_data["text"],
                    requires_params=template_data.get("requires_params", {}),
                    version=1,
                    is_active=True,
                )

                self.session.add(template)
                logger.info(f"Added template: {scenario_name}")
            except (KeyError, ValueError) as e:
                logger.error(f"Error initializing template for {scenario_name}: {e}")
                continue

        try:
            await self.session.commit()
            logger.info("Default templates initialized")
        except Exception as e:
            logger.error(f"Error committing templates: {e}")
            await self.session.rollback()

    async def get_response_template(self, scenario: str) -> Optional[ResponseTemplate]:
        """
        Get active response template for a scenario

        Args:
            scenario: Scenario name (e.g., "GREETING", "REFERRAL")

        Returns:
            ResponseTemplate or None if not found
        """
        try:
            # Handle ESCALATED scenario - use template from RESPONSE_TEMPLATES if not in DB
            if scenario == "ESCALATED":
                from app.utils.prompts import RESPONSE_TEMPLATES

                if "ESCALATED" in RESPONSE_TEMPLATES:
                    # Create temporary template object
                    class TempTemplate:
                        def __init__(self, text, params):
                            self.template_text = text
                            self.requires_params = params
                            self.version = 1
                            self.is_active = True

                    template_data = RESPONSE_TEMPLATES["ESCALATED"]
                    return TempTemplate(
                        template_data["text"], template_data.get("requires_params", {})
                    )

            result = await self.session.execute(
                select(ResponseTemplate)
                .where(
                    ResponseTemplate.scenario_name == ScenarioType[scenario],
                    ResponseTemplate.is_active == True,
                )
                .order_by(ResponseTemplate.version.desc())
            )
            template = result.scalar_one_or_none()

            if template:
                logger.debug(
                    f"Found template for scenario {scenario}: v{template.version}"
                )
            else:
                logger.warning(f"No template found for scenario {scenario}")

            return template

        except (KeyError, ValueError) as e:
            # Scenario not in enum - try RESPONSE_TEMPLATES as fallback
            logger.debug(f"Scenario {scenario} not in enum, trying RESPONSE_TEMPLATES")
            from app.utils.prompts import RESPONSE_TEMPLATES

            if scenario in RESPONSE_TEMPLATES:

                class TempTemplate:
                    def __init__(self, text, params):
                        self.template_text = text
                        self.requires_params = params
                        self.version = 1
                        self.is_active = True

                template_data = RESPONSE_TEMPLATES[scenario]
                return TempTemplate(
                    template_data["text"], template_data.get("requires_params", {})
                )

            logger.error(f"Error fetching template for {scenario}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching template for {scenario}: {str(e)}")
            return None

    def extract_params_from_message(self, message_text: str, scenario: str, client_id: Optional[str] = None) -> Dict[str, str]:
        """
        Extract parameters from message text for personalization
        
        Args:
            message_text: Original message text
            scenario: Detected scenario
        
        Returns:
            Dictionary of parameters for template
        """
        params = {}
        entities = self.entity_extractor.extract_entities(message_text)
        
        # Извлечь имя ребенка для персонализации
        # Использовать имя только если оно валидное (не приветствие, не слишком короткое)
        if entities["child_names"]:
            first_name = entities["child_names"][0]
            # Проверить, что это действительно имя (не приветствие)
            # Исключить короткие слова и приветствия
            name_lower = first_name.lower()
            exclude_names = {"привет", "здравствуйте", "добрый", "доброе"}
            
            # Имя должно быть длиннее 3 символов и не быть в списке исключений
            if len(first_name.replace(" ", "")) > 3 and name_lower not in exclude_names:
                # Дополнительная проверка: имя не должно быть первым словом сообщения (вероятно приветствие)
                # Разделить на слова и проверить первые 2 слова сообщения
                words_start = message_text.lower().split()[:2]
                # Разделить имя на слова
                name_words = name_lower.split()
                first_name_word = name_words[0] if name_words else ""
                
                # Если первое слово имени совпадает с первым словом сообщения - вероятно приветствие
                # Исключение: если перед именем есть другие слова (например, "Сегодня Владочка")
                is_greeting = False
                if words_start and first_name_word:
                    # Проверить, является ли первое слово имени первым или вторым словом сообщения
                    # И если это первое слово сообщения - это приветствие
                    if first_name_word == words_start[0]:
                        is_greeting = True
                    # Также проверить полное совпадение имени с первым словом
                    elif name_lower == words_start[0]:
                        is_greeting = True
                
                if not is_greeting:
                    params["child_name"] = first_name
        
        # Для ABSENCE_REQUEST - извлечь причину отсутствия
        if scenario == "ABSENCE_REQUEST":
            # Проверить полноту информации
            has_name = bool(params.get("child_name"))
            has_date = bool(entities["dates"])
            
            # Извлечь причину отсутствия из сообщения
            message_lower = message_text.lower()
            reason = None
            if "боле" in message_lower or "болезн" in message_lower:
                reason = "болезнь"
            elif "интернет" in message_lower or "интернета нет" in message_lower:
                reason = "проблемы с интернетом"
            elif "авария" in message_lower:
                reason = "авария"
            elif "справк" in message_lower:
                reason = "по справке"
            
            # Сформировать отсутствие note
            absence_note = "Отметил(а) отсутствие"
            if has_name:
                absence_note += f" {params['child_name']}"
            if has_date:
                absence_note += f" на {entities['dates'][0]}"
            else:
                absence_note += " на занятии"
            if reason:
                absence_note += f" (причина: {reason})"
            absence_note += "."
            
            params["absence_note"] = absence_note
            params["has_complete_info"] = has_name and has_date
            
            # Сформировать уточняющие вопросы если информации недостаточно
            additional_info = ""
            missing_info = []
            if not has_name:
                missing_info.append("имя ребенка")
            if not has_date:
                missing_info.append("дату отсутствия")
            
            if missing_info:
                questions_text = ", ".join(missing_info[:-1])
                if len(missing_info) > 1:
                    questions_text += f" и {missing_info[-1]}"
                else:
                    questions_text = missing_info[0]
                additional_info = f"\nДля точной отметки отсутствия мне нужна дополнительная информация: {questions_text}.\n"
            
            params["additional_info"] = additional_info
            params["missing_info"] = missing_info
            # По умолчанию отметка будет выполнена оператором
            params["crm_info"] = "Отметка отсутствия будет внесена в ваш личный кабинет в течение 24 часов."
            params["crm_status"] = "pending"
        
        # Для SCHEDULE_CHANGE - определить тип запроса
        if scenario == "SCHEDULE_CHANGE":
            schedule_note = "смене расписания/тренера"
            message_lower = message_text.lower()
            if "перенос" in message_lower or "перенести" in message_lower:
                schedule_note = "переносе занятия"
            elif "тренер" in message_lower or "смена тренера" in message_lower:
                schedule_note = "смене тренера"
            params["schedule_note"] = schedule_note
        
        # Для TECH_SUPPORT_BASIC - определить тип проблемы
        if scenario == "TECH_SUPPORT_BASIC":
            tech_note = ""
            message_lower = message_text.lower()
            if "ссылка" in message_lower or "не пришла ссылка" in message_lower:
                tech_note = "Если вам нужна ссылка на урок, она будет отправлена перед занятием."
            elif "пароль" in message_lower:
                tech_note = "Если проблема с паролем сохраняется, мы можем помочь его восстановить."
            params["tech_note"] = tech_note
        
        # Для REFERRAL - реферальная ссылка (из CRM если доступно)
        if scenario == "REFERRAL":
            if client_id:
                try:
                    crm_adapter = get_crm_adapter()
                    # Попытаться получить из CRM (асинхронно, но здесь синхронный контекст)
                    # В реальной реализации это будет вызываться асинхронно
                    params["referral_link"] = f"https://example.com/ref/{client_id}"
                except Exception as e:
                    logger.debug(f"Could not get referral link from CRM: {e}, using default")
                    params["referral_link"] = f"https://example.com/ref/{client_id}"
            else:
                params["referral_link"] = "https://example.com/referral"
        
        return params

    async def personalize_response(
        self, template_text: str, params: Dict[str, str] = None
    ) -> str:
        """
        Personalize response template with parameters

        Args:
            template_text: Template text with {param} placeholders
            params: Dictionary of parameters

        Returns:
            Personalized response text
        """
        if not params:
            params = {}

        try:
            # Заменить отсутствующие параметры на пустые строки или значения по умолчанию
            # Это позволит шаблонам работать даже если не все параметры заполнены
            default_params = {
                "child_name": "",
                "absence_note": "Отметил(а) отсутствие.",
                "additional_info": "",  # Уточняющие вопросы или пустая строка
                "crm_info": "Отметка отсутствия будет внесена в ваш личный кабинет в течение 24 часов.",
                "referral_link": "https://example.com/referral",
                "schedule_note": "смене расписания/тренера",
                "tech_note": "",
            }
            
            # Объединить дефолтные параметры с переданными
            final_params = {**default_params, **params}
            
            response = template_text.format(**final_params)
            logger.debug(f"Personalized response with params: {list(params.keys())}")
            return response

        except KeyError as e:
            logger.error(f"Missing parameter in template: {str(e)}")
            # Return template as-is if params missing
            return template_text

    async def get_response_text(
        self,
        scenario: str,
        params: Dict[str, str] = None,
    ) -> Optional[str]:
        """
        Get response text for a scenario without creating a database record
        
        Useful for combining multiple responses (e.g., greeting + main response)
        without creating unnecessary database entries.

        Args:
            scenario: Scenario name
            params: Parameters for personalization

        Returns:
            Response text or None if template not found
        """
        try:
            # Get template
            template = await self.get_response_template(scenario)
            if not template:
                logger.warning(f"No template found for scenario {scenario}")
                return None

            # Personalize
            response_text = await self.personalize_response(
                template.template_text, params
            )

            return response_text

        except Exception as e:
            logger.error(f"Error getting response text for {scenario}: {str(e)}")
            return None

    async def create_bot_response(
        self,
        scenario: str,
        client_id: str,
        original_message_id: str,
        params: Dict[str, str] = None,
        message_type: MessageType = MessageType.BOT_AUTO,
    ) -> Tuple[Optional[Message], Optional[str]]:
        """
        Create a bot response message

        Args:
            scenario: Scenario name
            client_id: Client ID
            original_message_id: ID of original message
            params: Parameters for personalization
            message_type: Type of message (auto, escalated, etc)

        Returns:
            (Message object, response_text) or (None, error_message)
        """
        try:
            # Get template
            template = await self.get_response_template(scenario)
            if not template:
                error_msg = f"No template found for scenario {scenario}"
                logger.warning(error_msg)
                return None, error_msg

            # Personalize
            response_text = await self.personalize_response(
                template.template_text, params
            )

            # Create message record
            message = Message(
                id=uuid.uuid4(),
                client_id=client_id,
                content=response_text,
                message_type=message_type,
                is_processed=True,
            )

            self.session.add(message)
            await self.session.flush()

            logger.info(
                f"Created bot response for client {client_id}: "
                f"scenario={scenario}, msg_id={message.id}"
            )

            return message, response_text

        except Exception as e:
            error_msg = f"Error creating bot response: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

    async def create_fallback_response(
        self, client_id: str, reason: str = "unknown"
    ) -> Tuple[Optional[Message], str]:
        """
        Create a fallback response (UNKNOWN scenario)

        Used when:
        - Classification fails
        - Confidence too low
        - No appropriate template
        """
        logger.info(f"Creating fallback response for {client_id}, reason: {reason}")

        return await self.create_bot_response(
            scenario="UNKNOWN",
            client_id=client_id,
            original_message_id="",
            message_type=MessageType.BOT_ESCALATED,
        )
