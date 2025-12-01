import logging
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.services.websocket_notifier import set_active_connections

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Store active WebSocket connections per operator
active_connections: Dict[str, List[WebSocket]] = {}

# Initialize websocket_notifier with connections
set_active_connections(active_connections)


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
    logger.info(
        f"✅ Operator {operator_id} connected. Active: {len(active_connections[operator_id])}"
    )

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


# Functions moved to app/services/websocket_notifier.py to avoid circular dependencies
# Re-export for backward compatibility
from app.services.websocket_notifier import notify_operator, notify_all_operators
