# connection_manager.py

import logging
import asyncio
from collections import defaultdict
from typing import Dict, List, Optional
import websockets
from splash_club.contracts import OutgoingMessage


class ConnectionManager:
    """Manages WebSocket connections and user-room relationships."""
    
    def __init__(self):
        # ROOM_ID -> USER_ID -> WebSocket
        self.users: Dict[str, Dict[str, websockets.ServerConnection]] = defaultdict(dict)
        # Map WebSocket back to user details for quick lookup
        self.websocket_to_user_info: Dict[websockets.ServerConnection, Dict[str, str]] = {}
        
    async def register_user(self, websocket: websockets.ServerConnection, room_id: str, user_id: str) -> None:
        """Register a user's websocket connection to a room."""
        self.users[room_id][user_id] = websocket
        self.websocket_to_user_info[websocket] = {"room_id": room_id, "user_id": user_id}
        logging.info(f"Registered user '{user_id}' to room '{room_id}' ({websocket.remote_address})")
        
    async def unregister_user(self, websocket: websockets.ServerConnection) -> Optional[str]:
        """Remove a user from tracking and return their room_id if they were in one."""
        user_info = self.websocket_to_user_info.pop(websocket, None)
        if user_info:
            room_id = user_info["room_id"]
            user_id = user_info["user_id"]
            logging.info(f"Unregistering user '{user_id}' from room '{room_id}' ({websocket.remote_address})")
            
            if room_id in self.users and user_id in self.users[room_id]:
                del self.users[room_id][user_id]
                if not self.users[room_id]:  # Room is empty
                    del self.users[room_id]
                    logging.info(f"Removed empty room '{room_id}'")
                    return None  # No need to notify if room is empty
                else:
                    return room_id  # Return room_id so caller can notify remaining users
            else:
                logging.warning(f"User '{user_id}' or room '{room_id}' not found during unregister")
        else:
            logging.debug(f"Websocket {websocket.remote_address} not found during unregister")
        return None
        
    def get_user_info(self, websocket: websockets.ServerConnection) -> Optional[Dict[str, str]]:
        """Get user info (room_id, user_id) for a websocket connection."""
        return self.websocket_to_user_info.get(websocket)
        
    def get_room_users(self, room_id: str) -> List[str]:
        """Get list of user IDs in a room."""
        return list(self.users.get(room_id, {}).keys())
        
    def room_exists(self, room_id: str) -> bool:
        """Check if a room has any active connections."""
        return room_id in self.users and bool(self.users[room_id])
        
    async def safe_websocket_send(self, websocket: websockets.ServerConnection, message_json: str) -> bool:
        """Safely send a JSON message, return False if connection failed."""
        try:
            await websocket.send(message_json)
            return True
        except websockets.exceptions.ConnectionClosed:
            logging.debug(f"Connection closed for {websocket.remote_address} during send attempt")
            return False
        except Exception as e:
            logging.error(f"Unexpected error sending to {websocket.remote_address}: {e}")
            return False
            
    async def broadcast_to_room(self, room_id: str, message: OutgoingMessage) -> int:
        """
        Broadcast a message to all users in a room.
        Returns the number of successful sends.
        """
        if not self.room_exists(room_id):
            logging.warning(f"Attempted to broadcast to non-existent room: {room_id}")
            return 0
            
        message_json = message.model_dump_json()
        current_connections = list(self.users[room_id].items())
        
        if not current_connections:
            logging.info(f"No active connections in room {room_id}")
            return 0
            
        logging.info(f"Broadcasting to room '{room_id}' ({len(current_connections)} users): {message.type}")
        
        tasks = [
            self.safe_websocket_send(ws, message_json)
            for _, ws in current_connections
        ]
        results = await asyncio.gather(*tasks)
        
        successful_sends = sum(1 for result in results if result)
        failed_sends = len(results) - successful_sends
        
        if failed_sends > 0:
            logging.warning(f"Failed to send to {failed_sends} users in room '{room_id}'")
            
        return successful_sends