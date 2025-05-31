import json
import logging
import websockets
from typing import Optional
from jill_box.contracts import IncomingMessage, parse_incoming_message
from pydantic import ValidationError

logger = logging.getLogger(__name__)

async def safe_websocket_send(websocket: websockets.ServerConnection, message_json: str) -> bool:
    """
    Safely sends a JSON message, returning False on connection failure.
    """
    try:
        await websocket.send(message_json)
        return True
    except websockets.exceptions.ConnectionClosed:
        logger.debug(f"Connection closed for {websocket.remote_address} during send attempt.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending to {websocket.remote_address}: {e}")
        return False

def parse_message_safely(message_str: str) -> tuple[Optional[IncomingMessage], Optional[str]]:
    """
    Safely parses a message string into an IncomingMessage.
    Returns (parsed_message, error_message) tuple.
    """
    try:
        parsed_message = parse_incoming_message(message_str)
        return parsed_message, None
    except ValidationError as e:
        error_msg = f"Validation error: {e.errors()}"
        logger.error(error_msg)
        return None, error_msg
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON format: {str(e)}"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Unexpected parsing error: {str(e)}"
        logger.error(error_msg)
        return None, error_msg