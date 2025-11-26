from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.schemas import MessageCreate, MessageResponse, MessageTypeEnum
from app.models.database import Message, MessageType
from app.database import get_session
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["messages"])

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Webhook endpoint для получения сообщений от чат-платформы.
    
    Expected JSON:
    {
        "client_id": "client_123",
        "content": "Привет, как работает реферальная программа?"
    }
    """
    try:
        # Create message record
        message = Message(
            id=uuid4(),
            client_id=message_data.client_id,
            content=message_data.content,
            message_type=MessageType.USER,
            is_processed=False,
        )
        
        session.add(message)
        await session.flush()  # Flush to get the ID
        
        logger.info(f"Message created: {message.id} for client: {message_data.client_id}")
        
        # TODO: Запустить классификацию (в следующем промпте)
        # TODO: Выбрать шаблон ответа
        # TODO: Отправить ответ обратно на платформу
        
        await session.commit()
        
        return MessageResponse(
            id=str(message.id),
            client_id=message.client_id,
            content=message.content,
            message_type=MessageTypeEnum(message.message_type.value),
            created_at=message.created_at,
        )
    
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )

@router.get("/{client_id}", response_model=list[MessageResponse])
async def get_client_messages(
    client_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get all messages for a specific client"""
    try:
        result = await session.execute(
            select(Message)
            .where(Message.client_id == client_id)
            .order_by(Message.created_at.desc())
        )
        messages = result.scalars().all()
        
        return [
            MessageResponse(
                id=str(m.id),
                client_id=m.client_id,
                content=m.content,
                message_type=MessageTypeEnum(m.message_type.value),
                created_at=m.created_at,
            )
            for m in messages
        ]
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch messages"
        )

