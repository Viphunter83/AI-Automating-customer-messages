from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Store active WebSocket connections per operator
active_connections: Dict[str, List[WebSocket]] = {}

@router.websocket("/ws/operator/{operator_id}")
async def websocket_operator(websocket: WebSocket, operator_id: str):
    """
    WebSocket endpoint for operator notifications
    
    Usage:
    ws = new WebSocket('ws://localhost:8000/ws/operator/op_123');
    ws.onmessage = (event) => { console.log(event.data); };
    """
    await websocket.accept()
    
    if operator_id not in active_connections:
        active_connections[operator_id] = []
    
    active_connections[operator_id].append(websocket)
    logger.info(f"✅ Operator {operator_id} connected. Active: {len(active_connections[operator_id])}")
    
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            
            # Echo back or process ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        logger.info(f"❌ Operator {operator_id} disconnected")
        if operator_id in active_connections:
            active_connections[operator_id].remove(websocket)
            
            if not active_connections[operator_id]:
                del active_connections[operator_id]

async def notify_operator(operator_id: str, message: dict):
    """
    Send notification to a specific operator
    
    Args:
        operator_id: ID of operator to notify
        message: Dict with notification data
    """
    if operator_id not in active_connections:
        logger.warning(f"Operator {operator_id} not connected")
        return
    
    disconnected = []
    for connection in active_connections[operator_id]:
        try:
            await connection.send_json(message)
            logger.debug(f"📨 Sent notification to {operator_id}")
        except Exception as e:
            logger.error(f"Error sending to {operator_id}: {str(e)}")
            disconnected.append(connection)
    
    # Remove disconnected connections
    for conn in disconnected:
        if conn in active_connections[operator_id]:
            active_connections[operator_id].remove(conn)
    
    if not active_connections[operator_id]:
        del active_connections[operator_id]

async def notify_all_operators(message: dict):
    """Send notification to all connected operators"""
    for operator_id in list(active_connections.keys()):
        await notify_operator(operator_id, message)

