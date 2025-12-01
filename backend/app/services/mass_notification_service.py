"""
Mass Notification Service
Handles mass notifications to all active clients (e.g., during mass outages)
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import ChatSession, DialogStatus, Message, MessageType
from app.services.response_manager import ResponseManager
from app.services.webhook_sender import WebhookSender

logger = logging.getLogger(__name__)


class MassNotificationService:
    """Service for sending mass notifications to active clients"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.response_manager = ResponseManager(session)
        self.webhook_sender = WebhookSender()

    async def get_active_clients(
        self, hours_active: int = 24
    ) -> List[str]:
        """
        Get list of active client IDs
        
        Args:
            hours_active: Consider clients active if they had activity in last N hours
            
        Returns:
            List of client_id strings
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_active)
        
        # Get active sessions (OPEN status) with recent activity
        result = await self.session.execute(
            select(ChatSession.client_id).where(
                and_(
                    ChatSession.status == DialogStatus.OPEN,
                    ChatSession.last_activity_at >= cutoff_time,
                )
            )
        )
        
        active_clients = [row[0] for row in result.all()]
        logger.info(f"Found {len(active_clients)} active clients (active in last {hours_active} hours)")
        
        return active_clients

    async def send_mass_outage_notification(
        self, client_ids: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Send mass outage notification to active clients
        
        Args:
            client_ids: Optional list of specific client IDs. If None, sends to all active clients.
            
        Returns:
            Dict with notification statistics
        """
        if client_ids is None:
            client_ids = await self.get_active_clients(hours_active=24)
        
        if not client_ids:
            logger.warning("No active clients found for mass notification")
            return {
                "success": False,
                "sent": 0,
                "failed": 0,
                "total": 0,
                "error": "No active clients found",
            }
        
        logger.info(f"🚨 Sending mass outage notification to {len(client_ids)} clients")
        
        sent_count = 0
        failed_count = 0
        
        # Create notification message for each client
        for client_id in client_ids:
            try:
                # Get last message from client (for context)
                result = await self.session.execute(
                    select(Message)
                    .where(Message.client_id == client_id)
                    .order_by(Message.created_at.desc())
                    .limit(1)
                )
                last_message = result.scalar_one_or_none()
                
                # Create mass outage response message
                response_msg, response_text = await self.response_manager.create_bot_response(
                    scenario="MASS_OUTAGE",
                    client_id=client_id,
                    original_message_id=str(last_message.id) if last_message else None,
                    params={},
                    message_type=MessageType.BOT_AUTO,
                )
                
                if response_msg:
                    # Send via webhook
                    webhook_result = await self.webhook_sender.send_response(
                        client_id=client_id,
                        response_text=response_text,
                        message_id=str(response_msg.id),
                        classification=None,
                    )
                    
                    if webhook_result.get("success"):
                        sent_count += 1
                        logger.debug(f"✅ Sent mass outage notification to {client_id}")
                    else:
                        failed_count += 1
                        logger.warning(
                            f"⚠️ Failed to send mass outage notification to {client_id}: "
                            f"{webhook_result.get('error')}"
                        )
                else:
                    failed_count += 1
                    logger.error(f"❌ Failed to create mass outage response for {client_id}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"❌ Error sending mass outage notification to {client_id}: "
                    f"{type(e).__name__}: {str(e)}",
                    exc_info=True,
                )
        
        result = {
            "success": sent_count > 0,
            "sent": sent_count,
            "failed": failed_count,
            "total": len(client_ids),
            "sent_at": datetime.utcnow(),
        }
        
        logger.info(
            f"📊 Mass outage notification completed: {sent_count} sent, "
            f"{failed_count} failed out of {len(client_ids)} total"
        )
        
        return result

