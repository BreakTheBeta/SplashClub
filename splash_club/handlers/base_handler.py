from abc import ABC, abstractmethod
import logging
import websockets
from typing import Optional, Dict
from splash_club.contracts import IncomingMessage, UserUpdateServerMessage
from splash_club.utils.error_handling import send_typed_error_message, send_generic_error
from splash_club.connection_manager import ConnectionManager
from splash_club.game import GameGateway

logger = logging.getLogger(__name__)

class BaseHandler(ABC):
    """Base class for all message handlers."""
    
    def __init__(self, connection_manager: ConnectionManager, game_gateway: GameGateway, game_state_manager=None):
        self.connection_manager = connection_manager
        self.game_gateway = game_gateway
        self.game_state_manager = game_state_manager
    
    @abstractmethod
    async def handle(self, websocket: websockets.ServerConnection, message) -> bool:
        """
        Handle the incoming message.
        Returns True if handled successfully, False otherwise.
        """
        pass
    
    async def send_error(
        self, 
        websocket: websockets.ServerConnection, 
        error_code_enum_member, 
        request_id: Optional[str] = None
    ) -> bool:
        """Send a typed error message using enum member."""
        return await send_typed_error_message(websocket, error_code_enum_member, request_id)
    
    async def send_generic_error(
        self, 
        websocket: websockets.ServerConnection, 
        message: str, 
        request_id: Optional[str] = None
    ) -> bool:
        """Send a generic error message."""
        return await send_generic_error(websocket, message, request_id)
    
    def get_user_context(self, websocket: websockets.ServerConnection) -> Optional[Dict[str, str]]:
        """
        Get the current user's room, user ID, and name from the websocket.
        Returns dict with room_id, user_id, and user_name, or None if not authenticated.
        """
        return self.connection_manager.get_user_info(websocket)
    
    def validate_user_in_room(
        self, 
        websocket: websockets.ServerConnection, 
        expected_room_id: str, 
        expected_user_id: str
    ) -> bool:
        """
        Validate that the websocket user matches the expected room and user.
        Returns True if valid, False otherwise.
        """
        user_info = self.get_user_context(websocket)
        if not user_info:
            return False
            
        current_room_id = user_info.get("room_id")
        current_user_id = user_info.get("user_id")
        
        if current_room_id != expected_room_id or current_user_id != expected_user_id:
            logger.warning(
                f"User validation failed: expected room='{expected_room_id}', "
                f"user='{expected_user_id}' vs actual room='{current_room_id}', "
                f"user='{current_user_id}' for {websocket.remote_address}"
            )
            return False
        return True

    async def notify_room_users_updated(self, room_id: str) -> bool:
        """
        Notify all users in a room about user list updates.
        Returns True if notification was sent successfully.
        """
        try:
            users = self.connection_manager.get_room_users(room_id)
            message = UserUpdateServerMessage(
                users=users  # users is already a List[str], no need to extract ["id"]
            )
            await self.connection_manager.broadcast_to_room(room_id, message)
            return True
        except Exception as e:
            logger.error(f"Failed to notify room '{room_id}' of user updates: {e}")
            return False