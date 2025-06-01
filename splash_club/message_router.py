import logging
from typing import Dict, Type, Protocol
import websockets
from splash_club.contracts import IncomingMessage
from splash_club.handlers.base_handler import BaseHandler
from splash_club.handlers.room_handlers import CreateRoomHandler, JoinRoomHandler, ReJoinRoomHandler
from splash_club.handlers.game_handlers import StartRoomHandler, SubmitAnswerHandler, SubmitVoteHandler
from splash_club.utils.error_handling import send_generic_error

logger = logging.getLogger(__name__)

class HandlerFactory(Protocol):
    def create_handlers(self) -> Dict[str, BaseHandler]:
        ...

class MessageRouter:
    def __init__(self, connection_manager, game_gateway, game_state_manager):
        self.connection_manager = connection_manager
        self.game_gateway = game_gateway
        self.game_state_manager = game_state_manager
        self.handlers = self._create_handlers()
    
    def _create_handlers(self) -> Dict[str, BaseHandler]:
        """Create and return all message handlers."""
        return {
            "create_room": CreateRoomHandler(
                self.connection_manager, 
                self.game_gateway
            ),
            "join_room": JoinRoomHandler(
                self.connection_manager, 
                self.game_gateway
            ),
            "rejoin_room": ReJoinRoomHandler(
                self.connection_manager, 
                self.game_gateway
            ),
            "start_room": StartRoomHandler(
                self.connection_manager, 
                self.game_gateway, 
                self.game_state_manager
            ),
            "submit_answer": SubmitAnswerHandler(
                self.connection_manager, 
                self.game_gateway, 
                self.game_state_manager
            ),
            "submit_vote": SubmitVoteHandler(
                self.connection_manager, 
                self.game_gateway, 
                self.game_state_manager
            ),
        }
    
    async def route_message(
        self, 
        websocket: websockets.ServerConnection, 
        parsed_message: IncomingMessage
    ) -> bool:
        """
        Route a parsed message to the appropriate handler.
        Returns True if message was handled successfully, False otherwise.
        """
        message_type = parsed_message.type
        handler = self.handlers.get(message_type)
        
        if not handler:
            logger.warning(f"No handler found for message type: {message_type}")
            await send_generic_error(
                websocket, 
                f"Unknown message type: {message_type}",
                parsed_message.request_id
            )
            return False
        
        try:
            return await handler.handle(websocket, parsed_message)
        except Exception as e:
            logger.exception(f"Handler error for {message_type}: {e}")
            await send_generic_error(
                websocket, 
                "Internal server error",
                parsed_message.request_id
            )
            return False