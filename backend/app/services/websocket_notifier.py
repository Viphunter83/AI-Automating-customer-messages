"""
WebSocket Notification Service
Handles WebSocket notifications to operators
Separated from routes to avoid circular dependencies
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Store active WebSocket connections per operator
# This will be initialized from routes/ws.py
_active_connections: Dict[str, list] = {}


def set_active_connections(connections: Dict[str, list]):
    """Set active connections dictionary (called from routes/ws.py)"""
    global _active_connections
    _active_connections = connections


async def notify_operator(operator_id: str, message: dict):
    """
    Send notification to a specific operator
    
    Args:
        operator_id: ID of operator to notify
        message: Dict with notification data
    """
    if operator_id not in _active_connections:
        logger.debug(f"Operator {operator_id} not connected")
        return

    disconnected = []
    for connection in _active_connections[operator_id]:
        try:
            await connection.send_json(message)
            logger.debug(f"📨 Sent notification to {operator_id}")
        except Exception as e:
            logger.error(f"Error sending to {operator_id}: {str(e)}")
            disconnected.append(connection)

    # Remove disconnected connections
    for conn in disconnected:
        if conn in _active_connections[operator_id]:
            _active_connections[operator_id].remove(conn)

    if not _active_connections[operator_id]:
        del _active_connections[operator_id]


async def notify_all_operators(message: dict):
    """Send notification to all connected operators"""
    for operator_id in list(_active_connections.keys()):
        await notify_operator(operator_id, message)

