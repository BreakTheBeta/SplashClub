import logging
import websockets
from typing import Optional
from splash_club.contracts import ErrorServerMessage, RoomNotFoundServerMessage
from .websocket_utils import safe_websocket_send

logger = logging.getLogger(__name__)

async def send_typed_error_message(
    websocket: websockets.ServerConnection, 
    error_code_enum_member, 
    request_id: Optional[str] = None
) -> bool:
    """Sends a Pydantic ErrorServerMessage using the enum member's name."""
    error_msg = ErrorServerMessage(
        message=error_code_enum_member.name, 
        response_to_request_id=request_id
    )
    success = await safe_websocket_send(websocket, error_msg.model_dump_json())
    if not success:
        logger.warning(f"Failed to send error to {websocket.remote_address}")
    return success

async def send_room_not_found(websocket: websockets.ServerConnection) -> bool:
    """Sends a RoomNotFoundServerMessage."""
    error_msg = RoomNotFoundServerMessage()
    success = await safe_websocket_send(websocket, error_msg.model_dump_json())
    if not success:
        logger.warning(f"Failed to send room not found error to {websocket.remote_address}")
    return success

async def send_generic_error(
    websocket: websockets.ServerConnection, 
    message: str, 
    request_id: Optional[str] = None
) -> bool:
    """Sends a generic error message."""
    error_msg = ErrorServerMessage(message=message, response_to_request_id=request_id)
    success = await safe_websocket_send(websocket, error_msg.model_dump_json())
    if not success:
        logger.warning(f"Failed to send generic error to {websocket.remote_address}")
    return success