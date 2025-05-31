import asyncio
import logging
import websockets
from typing import Optional
from jill_box.connection_manager import ConnectionManager
from jill_box.message_router import MessageRouter
from jill_box.game_state_manager import GameStateManager
from jill_box.game import GameGateway
from jill_box.utils.websocket_utils import parse_message_safely
from jill_box.utils.error_handling import send_generic_error

logger = logging.getLogger(__name__)

class WebSocketServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 6969):
        self.host = host
        self.port = port
        
        # Initialize core components
        self.connection_manager = ConnectionManager()
        self.game_gateway = GameGateway()
        self.game_state_manager = GameStateManager(
            self.connection_manager, 
            self.game_gateway
        )
        self.message_router = MessageRouter(
            self.connection_manager, 
            self.game_gateway, 
            self.game_state_manager
        )
    
    async def handle_connection(self, websocket: websockets.ServerConnection):
        """Handle a single WebSocket connection throughout its lifecycle."""
        client_address = websocket.remote_address
        logger.info(f"Client connected: {client_address}")
        
        try:
            async for message_str in websocket:
                await self._process_message(websocket, str(message_str))
                
        except websockets.exceptions.ConnectionClosedOK:
            logger.info(f"Client disconnected gracefully: {client_address}")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.warning(f"Client connection closed with error: {client_address}, Error: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error in connection handler for {client_address}: {e}")
        finally:
            await self.connection_manager.unregister_user(websocket)
            logger.info(f"Client connection cleaned up: {client_address}")
    
    async def _process_message(self, websocket: websockets.ServerConnection, message_str: str):
        """Process a single message from a WebSocket connection."""
        # Parse the message
        parsed_message, parse_error = parse_message_safely(message_str)
        
        if parsed_message is None:
            logger.error(f"Failed to parse message from {websocket.remote_address}: {parse_error}")
            await send_generic_error(websocket, f"Message parsing failed: {parse_error}")
            return
        
        logger.info(f"Received '{parsed_message.type}' from {websocket.remote_address}")
        
        # Route the message to appropriate handler
        success = await self.message_router.route_message(websocket, parsed_message)
        
        if not success:
            logger.warning(f"Failed to handle {parsed_message.type} from {websocket.remote_address}")
    
    async def start(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        
        async with websockets.serve(self.handle_connection, self.host, self.port):
            # Keep the server running
            await asyncio.Future()
    
    async def shutdown(self):
        """Gracefully shutdown the server."""
        logger.info("Shutting down WebSocket server...")
        # Could add cleanup logic here if needed
        # For now, the context manager in start() handles cleanup