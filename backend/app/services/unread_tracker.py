"""
Unread Message Tracker Service
Tracks which messages operators have read for unread indicators
"""
import logging
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import Message, OperatorMessageRead

logger = logging.getLogger(__name__)


class UnreadTrackerService:
    """Service for tracking unread messages per operator"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def mark_messages_as_read(
        self, operator_id: str, client_id: str, message_id: Optional[UUID] = None
    ) -> OperatorMessageRead:
        """
        Mark messages as read for an operator-client pair
        
        Args:
            operator_id: Operator ID
            client_id: Client ID
            message_id: Optional specific message ID to mark as read.
                       If None, marks all messages up to the latest as read.
        
        Returns:
            OperatorMessageRead object
        """
        try:
            # Check if read record exists
            result = await self.session.execute(
                select(OperatorMessageRead).where(
                    OperatorMessageRead.operator_id == operator_id,
                    OperatorMessageRead.client_id == client_id,
                )
            )
            read_record = result.scalar_one_or_none()

            # If no message_id provided, get the latest message for this client
            if message_id is None:
                latest_message_result = await self.session.execute(
                    select(Message.id)
                    .where(Message.client_id == client_id)
                    .order_by(Message.created_at.desc())
                    .limit(1)
                )
                message_id = latest_message_result.scalar_one_or_none()

            if message_id is None:
                # No messages for this client yet
                logger.debug(f"No messages found for client {client_id}")
                # Still create/update read record
                if read_record:
                    read_record.last_read_at = datetime.utcnow()
                    read_record.updated_at = datetime.utcnow()
                else:
                    read_record = OperatorMessageRead(
                        operator_id=operator_id,
                        client_id=client_id,
                        last_read_message_id=None,
                        last_read_at=datetime.utcnow(),
                    )
                    self.session.add(read_record)
                await self.session.flush()
                return read_record

            # Update or create read record
            if read_record:
                read_record.last_read_message_id = message_id
                read_record.last_read_at = datetime.utcnow()
                read_record.updated_at = datetime.utcnow()
            else:
                read_record = OperatorMessageRead(
                    operator_id=operator_id,
                    client_id=client_id,
                    last_read_message_id=message_id,
                    last_read_at=datetime.utcnow(),
                )
                self.session.add(read_record)

            await self.session.flush()
            logger.debug(
                f"✅ Marked messages as read for operator {operator_id}, client {client_id}, message {message_id}"
            )
            return read_record

        except Exception as e:
            logger.error(f"Error marking messages as read: {str(e)}")
            raise

    async def get_unread_count(
        self, operator_id: str, client_id: str
    ) -> int:
        """
        Get count of unread messages for an operator-client pair
        
        Args:
            operator_id: Operator ID
            client_id: Client ID
        
        Returns:
            Number of unread messages
        """
        try:
            # Get last read message ID
            read_result = await self.session.execute(
                select(OperatorMessageRead).where(
                    OperatorMessageRead.operator_id == operator_id,
                    OperatorMessageRead.client_id == client_id,
                )
            )
            read_record = read_result.scalar_one_or_none()

            if not read_record or not read_record.last_read_message_id:
                # No read record or no last read message - count all messages
                count_result = await self.session.execute(
                    select(func.count(Message.id)).where(
                        Message.client_id == client_id,
                        Message.message_type.in_(["user", "bot_auto", "bot_escalated"]),
                    )
                )
                return count_result.scalar_one() or 0

            # Count messages created after last read
            count_result = await self.session.execute(
                select(func.count(Message.id)).where(
                    Message.client_id == client_id,
                    Message.message_type.in_(["user", "bot_auto", "bot_escalated"]),
                    Message.created_at > read_record.last_read_at,
                )
            )
            return count_result.scalar_one() or 0

        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0

    async def get_unread_counts_for_all_clients(
        self, operator_id: str
    ) -> Dict[str, int]:
        """
        Get unread counts for all clients for an operator
        
        Args:
            operator_id: Operator ID
        
        Returns:
            Dictionary mapping client_id to unread count
        """
        try:
            # Get all read records for this operator
            read_records_result = await self.session.execute(
                select(OperatorMessageRead).where(
                    OperatorMessageRead.operator_id == operator_id
                )
            )
            read_records = read_records_result.scalars().all()

            # Get all unique client_ids from messages
            clients_result = await self.session.execute(
                select(Message.client_id)
                .distinct()
                .where(Message.message_type.in_(["user", "bot_auto", "bot_escalated"]))
            )
            all_clients = set(clients_result.scalars().all())

            unread_counts = {}

            # For each client, calculate unread count
            for client_id in all_clients:
                read_record = next(
                    (r for r in read_records if r.client_id == client_id), None
                )

                if not read_record or not read_record.last_read_message_id:
                    # Count all messages
                    count_result = await self.session.execute(
                        select(func.count(Message.id)).where(
                            Message.client_id == client_id,
                            Message.message_type.in_(["user", "bot_auto", "bot_escalated"]),
                        )
                    )
                    unread_counts[client_id] = count_result.scalar_one() or 0
                else:
                    # Count messages after last read
                    count_result = await self.session.execute(
                        select(func.count(Message.id)).where(
                            Message.client_id == client_id,
                            Message.message_type.in_(["user", "bot_auto", "bot_escalated"]),
                            Message.created_at > read_record.last_read_at,
                        )
                    )
                    unread_counts[client_id] = count_result.scalar_one() or 0

            return unread_counts

        except Exception as e:
            logger.error(f"Error getting unread counts for all clients: {str(e)}")
            return {}

