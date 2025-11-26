import logging
from typing import Dict, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import ResponseTemplate, Message, MessageType, ScenarioType
from app.utils.prompts import RESPONSE_TEMPLATES
import uuid

logger = logging.getLogger(__name__)

class ResponseManager:
    """Manage response templates and selection"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def initialize_default_templates(self) -> None:
        """
        Initialize default response templates in database
        Called once during app startup
        """
        logger.info("Initializing default response templates...")
        
        for scenario_name, template_data in RESPONSE_TEMPLATES.items():
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
        
        await self.session.commit()
        logger.info("Default templates initialized")
    
    async def get_response_template(
        self,
        scenario: str
    ) -> Optional[ResponseTemplate]:
        """
        Get active response template for a scenario
        
        Args:
            scenario: Scenario name (e.g., "GREETING", "REFERRAL")
        
        Returns:
            ResponseTemplate or None if not found
        """
        try:
            result = await self.session.execute(
                select(ResponseTemplate).where(
                    ResponseTemplate.scenario_name == ScenarioType[scenario],
                    ResponseTemplate.is_active == True,
                ).order_by(ResponseTemplate.version.desc())
            )
            template = result.scalar_one_or_none()
            
            if template:
                logger.debug(f"Found template for scenario {scenario}: v{template.version}")
            else:
                logger.warning(f"No template found for scenario {scenario}")
            
            return template
        
        except Exception as e:
            logger.error(f"Error fetching template for {scenario}: {str(e)}")
            return None
    
    async def personalize_response(
        self,
        template_text: str,
        params: Dict[str, str] = None
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
            response = template_text.format(**params)
            logger.debug(f"Personalized response with params: {list(params.keys())}")
            return response
        
        except KeyError as e:
            logger.error(f"Missing parameter in template: {str(e)}")
            # Return template as-is if params missing
            return template_text
    
    async def create_bot_response(
        self,
        scenario: str,
        client_id: str,
        original_message_id: str,
        params: Dict[str, str] = None,
        message_type: MessageType = MessageType.BOT_AUTO
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
                template.template_text,
                params
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
        self,
        client_id: str,
        reason: str = "unknown"
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
            message_type=MessageType.BOT_ESCALATED
        )
