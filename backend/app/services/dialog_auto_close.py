import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.database import (
    ChatSession,
    DialogStatus,
    Message,
    MessageType,
    ScenarioType,
)
from app.services.response_manager import ResponseManager
from app.services.webhook_sender import WebhookSender

logger = logging.getLogger(__name__)


class DialogAutoCloseService:
    """Service for managing automatic dialog closure"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.inactivity_timeout_minutes = 3  # Close after 3 minutes of inactivity
        self.farewell_delay_minutes = 2  # Send farewell after 2 minutes

    async def get_or_create_session(self, client_id: str) -> ChatSession:
        """Get existing session or create a new one"""
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.client_id == client_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            session = ChatSession(
                id=uuid.uuid4(),
                client_id=client_id,
                status=DialogStatus.OPEN,
                last_activity_at=datetime.utcnow(),
            )
            self.session.add(session)
            await self.session.flush()
            logger.debug(f"Created new chat session for client {client_id}")

        return session

    async def update_activity(self, client_id: str) -> None:
        """Update last activity timestamp for a client"""
        session = await self.get_or_create_session(client_id)

        # If session was closed, reopen it
        if session.status == DialogStatus.CLOSED:
            session.status = DialogStatus.OPEN
            session.closed_at = None
            session.farewell_sent_at = None
            logger.info(f"Reopened closed session for client {client_id}")

        session.last_activity_at = datetime.utcnow()
        await self.session.flush()
        logger.debug(f"Updated activity for client {client_id}")

    async def get_inactive_sessions(
        self, minutes: Optional[int] = None
    ) -> List[ChatSession]:
        """Get sessions that have been inactive for specified minutes"""
        if minutes is None:
            minutes = self.inactivity_timeout_minutes

        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        result = await self.session.execute(
            select(ChatSession).where(
                and_(
                    ChatSession.status == DialogStatus.OPEN,
                    ChatSession.last_activity_at <= cutoff_time,
                )
            )
        )

        return result.scalars().all()

    async def get_sessions_needing_farewell(
        self, minutes: Optional[int] = None
    ) -> List[ChatSession]:
        """Get open sessions that need farewell message"""
        if minutes is None:
            minutes = self.farewell_delay_minutes

        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        result = await self.session.execute(
            select(ChatSession).where(
                and_(
                    ChatSession.status == DialogStatus.OPEN,
                    ChatSession.last_activity_at <= cutoff_time,
                    ChatSession.farewell_sent_at.is_(None),
                )
            )
        )

        return result.scalars().all()

    async def send_farewell_message(self, client_id: str) -> Optional[Dict]:
        """Send farewell message to client with delay"""
        try:
            session = await self.get_or_create_session(client_id)

            # Check if farewell already sent
            if session.farewell_sent_at:
                logger.debug(f"Farewell already sent for client {client_id}")
                return None

            # Get last message from client
            result = await self.session.execute(
                select(Message)
                .where(Message.client_id == client_id)
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            last_message = result.scalar_one_or_none()

            if not last_message:
                logger.warning(f"No messages found for client {client_id}")
                return None

            # Add delay before sending farewell (simulate natural conversation pause)
            settings = get_settings()
            if settings.delays_enabled and settings.farewell_delay_seconds > 0:
                delay = settings.farewell_delay_seconds
                logger.debug(
                    f"⏳ Delaying farewell by {delay:.1f} seconds for client {client_id}"
                )
                await asyncio.sleep(delay)

            # Create farewell response
            response_manager = ResponseManager(self.session)
            response_msg, response_text = await response_manager.create_bot_response(
                scenario=ScenarioType.FAREWELL.value,
                client_id=client_id,
                original_message_id=str(last_message.id),
                message_type=MessageType.BOT_AUTO,
            )

            if not response_msg:
                logger.error(f"Failed to create farewell response for {client_id}")
                return None

            # Send via webhook
            webhook_sender = WebhookSender()
            webhook_result = await webhook_sender.send_response(
                client_id=client_id,
                response_text=response_text,
                message_id=str(response_msg.id),
                classification={"scenario": "FAREWELL", "confidence": 1.0},
            )

            # Mark farewell as sent
            session.farewell_sent_at = datetime.utcnow()
            await self.session.flush()

            logger.info(f"Sent farewell message to client {client_id}")

            return {
                "success": True,
                "message_id": str(response_msg.id),
                "webhook_result": webhook_result,
            }

        except Exception as e:
            logger.error(
                f"Error sending farewell to {client_id}: {str(e)}", exc_info=True
            )
            return {"success": False, "error": str(e)}

    async def close_session(self, client_id: str) -> bool:
        """Close a chat session"""
        try:
            session = await self.get_or_create_session(client_id)

            if session.status == DialogStatus.CLOSED:
                logger.debug(f"Session already closed for client {client_id}")
                return True

            session.status = DialogStatus.CLOSED
            session.closed_at = datetime.utcnow()
            await self.session.flush()

            logger.info(f"Closed session for client {client_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error closing session for {client_id}: {str(e)}", exc_info=True
            )
            return False

    async def process_inactive_sessions(self) -> Dict[str, int]:
        """Process all inactive sessions: send farewell and close"""
        stats = {"farewell_sent": 0, "sessions_closed": 0, "errors": 0}

        # First, send farewell to sessions that need it
        sessions_needing_farewell = await self.get_sessions_needing_farewell()

        for session in sessions_needing_farewell:
            result = await self.send_farewell_message(session.client_id)
            if result and result.get("success"):
                stats["farewell_sent"] += 1
            else:
                stats["errors"] += 1

        await self.session.commit()

        # Then, close sessions that have been inactive long enough
        # Only close sessions where:
        # 1. Farewell was sent AND enough time has passed since farewell (1 minute after farewell = 3 minutes total)
        # 2. OR no farewell was sent but timeout exceeded (fallback for edge cases)
        inactive_sessions = await self.get_inactive_sessions()
        now = datetime.utcnow()

        for session in inactive_sessions:
            should_close = False

            if session.farewell_sent_at:
                # Farewell was sent - close only if enough time passed since farewell
                # We sent farewell at farewell_delay_minutes (2 min), so we need to wait
                # additional (inactivity_timeout_minutes - farewell_delay_minutes) = 1 minute
                time_since_farewell = (
                    now - session.farewell_sent_at
                ).total_seconds() / 60
                time_since_activity = (
                    now - session.last_activity_at
                ).total_seconds() / 60

                # Close if farewell was sent AND total inactivity >= timeout
                should_close = (
                    time_since_farewell
                    >= (self.inactivity_timeout_minutes - self.farewell_delay_minutes)
                    and time_since_activity >= self.inactivity_timeout_minutes
                )
            else:
                # No farewell sent - close if timeout exceeded (fallback case)
                time_since_activity = (
                    now - session.last_activity_at
                ).total_seconds() / 60
                should_close = time_since_activity >= self.inactivity_timeout_minutes

            if should_close:
                success = await self.close_session(session.client_id)
                if success:
                    stats["sessions_closed"] += 1
                else:
                    stats["errors"] += 1

        await self.session.commit()

        logger.info(f"Processed inactive sessions: {stats}")
        return stats
