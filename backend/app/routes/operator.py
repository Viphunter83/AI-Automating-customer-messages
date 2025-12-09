"""
Operator API endpoints
Allows operators to send messages to clients and manage conversations
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_operator
from app.database import get_session
from app.integrations.telegram.sender import TelegramResponseSender
from app.models.database import Message, MessageType
from app.models.schemas import MessageCreate
from app.services.dialog_auto_close import DialogAutoCloseService
from app.routes.telegram import get_telegram_bot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/operator", tags=["operator"])


@router.post("/send-message")
async def send_operator_message(
    request_data: dict,
    operator_id: str = Depends(get_current_operator),
    session: AsyncSession = Depends(get_session),
):
    """
    Send a message from operator to client
    
    This endpoint allows operators to respond to clients through the system.
    Messages are saved in the database and delivered via webhook.
    
    Request body:
    {
        "client_id": "telegram_123456",
        "content": "Ваше сообщение"
    }
    """
    client_id = request_data.get("client_id")
    content = request_data.get("content")
    
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty"
        )
    
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id is required"
        )
    
    try:
        # Create operator message in database
        operator_message = Message(
            client_id=client_id,
            content=content,
            message_type=MessageType.OPERATOR,
            is_processed=True,
        )
        session.add(operator_message)
        await session.flush()
        
        # Update dialog activity
        dialog_service = DialogAutoCloseService(session)
        await dialog_service.update_activity(client_id)
        
        # Send message to client via webhook
        # Check if client is Telegram client
        if client_id.startswith("telegram_"):
            # Extract chat_id from client_id
            try:
                chat_id = int(client_id.replace("telegram_", ""))
                bot = get_telegram_bot()
                if bot:
                    sender = TelegramResponseSender(bot.bot)
                    result = await sender.send_response(
                        chat_id=chat_id,
                        response_text=content,
                        message_id=str(operator_message.id),
                    )
                    if not result.get("success"):
                        logger.error(f"Failed to send Telegram message: {result.get('error')}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to send message: {result.get('error')}"
                        )
                else:
                    logger.warning("Telegram bot not initialized, cannot send message")
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Telegram bot not available"
                    )
            except ValueError:
                logger.error(f"Invalid Telegram client_id format: {client_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid client_id format for Telegram"
                )
        else:
            # For non-Telegram clients, use webhook mechanism
            # This would require webhook_url from ChatSession
            # For now, just save the message
            logger.info(f"Non-Telegram client {client_id}, message saved but not delivered via webhook")
            # TODO: Implement webhook delivery for non-Telegram clients
        
        await session.commit()
        
        logger.info(
            f"✅ Operator {operator_id} sent message to client {client_id}: "
            f"{content[:50]}..."
        )
        
        return {
            "success": True,
            "message_id": str(operator_message.id),
            "client_id": client_id,
            "content": content,
            "sent_at": operator_message.created_at.isoformat(),
        }
        
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error sending operator message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/telegram-file-url/{file_id}")
async def get_telegram_file_url(
    file_id: str,
    operator_id: str = Depends(get_current_operator),
):
    """
    Get download URL for a Telegram file
    
    This endpoint allows operators to view media files (photos, documents) 
    sent by clients through Telegram.
    """
    bot = get_telegram_bot()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot not available"
        )
    
    try:
        # Get file info from Telegram
        file_info = await bot.bot.get_file(file_id)
        
        # Construct download URL
        # Telegram file URLs are: https://api.telegram.org/file/bot<token>/<file_path>
        file_url = file_info.file_path
        if file_url:
            # Return the file path that can be used to construct full URL
            # Frontend will construct: https://api.telegram.org/file/bot<TOKEN>/<file_path>
            # But we should return a proxy URL for security (don't expose bot token)
            return {
                "success": True,
                "file_id": file_id,
                "file_path": file_url,
                "file_size": file_info.file_size,
                # Return proxy URL instead of direct Telegram URL
                "proxy_url": f"/api/operator/telegram-file/{file_id}",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
            
    except Exception as e:
        logger.error(f"Error getting Telegram file URL: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file URL: {str(e)}"
        )


@router.get("/telegram-file/{file_id}")
async def proxy_telegram_file(
    file_id: str,
    operator_id: str = Depends(get_current_operator),
):
    """
    Proxy endpoint for downloading Telegram files
    
    This endpoint downloads the file from Telegram and streams it to the operator,
    without exposing the bot token to the frontend.
    """
    import httpx
    
    bot = get_telegram_bot()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot not available"
        )
    
    try:
        # Get file info from Telegram
        file_info = await bot.bot.get_file(file_id)
        
        if not file_info.file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Construct Telegram file URL
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
        
        # Download file and stream to client
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to download file from Telegram"
                )
            
            # Determine content type
            content_type = response.headers.get("content-type", "application/octet-stream")
            
            return StreamingResponse(
                iter([response.content]),
                media_type=content_type,
                headers={
                    "Content-Disposition": f'inline; filename="{file_info.file_path.split("/")[-1]}"'
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error proxying Telegram file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to proxy file: {str(e)}"
        )

