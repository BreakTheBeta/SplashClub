# handlers/room_handlers.py

import time
import logging
import websockets
from .base_handler import BaseHandler
from splash_club.contracts import (
    CreateRoomClientMessage, JoinRoomClientMessage, ReJoinRoomClientMessage,
    JoinRoomSuccessServerMessage, ReJoinRoomSuccessServerMessage, RoomNotFoundServerMessage
)
from splash_club.game import PromptRoom, JoinReturnCodes
from splash_club.connection_manager import ConnectionManager


class CreateRoomHandler(BaseHandler):
    """Handles room creation requests."""
    
    async def handle(self, websocket: websockets.ServerConnection, message: CreateRoomClientMessage) -> bool:
        try:
            # Create new room through game gateway
            room_id = self.game_gateway.new_game(PromptRoom)
            user_id = message.user
            
            # Try to join the newly created room
            ret_join = self.game_gateway.join_room(room_id, user_id)
            
            if ret_join == JoinReturnCodes.SUCCESS:
                # Register user connection
                await self.connection_manager.register_user(websocket, room_id, user_id)
                
                # Send success response
                join_ok_msg = JoinRoomSuccessServerMessage(
                    room=room_id, 
                    user=user_id, 
                    response_to_request_id=message.request_id
                )
                await self.connection_manager.safe_websocket_send(websocket, join_ok_msg.model_dump_json())
                
                # Notify other users (though for new room, this user is the only one)
                await self.notify_room_users_updated(room_id)
                
                logging.info(f"User '{user_id}' created and joined room '{room_id}'")
                return True
            else:
                await self.send_error(websocket, ret_join, message.request_id)
                return False
                
        except Exception as e:
            logging.error(f"Error creating room for user '{message.user}': {e}")
            await self.send_generic_error(websocket, "Failed to create room", message.request_id)
            return False


class JoinRoomHandler(BaseHandler):
    """Handles room joining requests."""
    
    async def handle(self, websocket: websockets.ServerConnection, message: JoinRoomClientMessage) -> bool:
        try:
            room_id = message.room
            user_id = message.user
            
            # Try to join room through game gateway
            ret_join = self.game_gateway.join_room(room_id, user_id)
            
            if ret_join == JoinReturnCodes.SUCCESS:
                # Register user connection
                await self.connection_manager.register_user(websocket, room_id, user_id)
                
                # Send success response
                join_ok_msg = JoinRoomSuccessServerMessage(
                    room=room_id, 
                    user=user_id, 
                    response_to_request_id=message.request_id
                )
                await self.connection_manager.safe_websocket_send(websocket, join_ok_msg.model_dump_json())
                
                # Small delay to ensure message ordering (as in original)
                time.sleep(0.1)
                
                # Notify all users in room about the new user
                await self.notify_room_users_updated(room_id)
                
                logging.info(f"User '{user_id}' joined room '{room_id}'")
                return True
            else:
                await self.send_error(websocket, ret_join, message.request_id)
                return False
                
        except Exception as e:
            logging.error(f"Error joining room '{message.room}' for user '{message.user}': {e}")
            await self.send_generic_error(websocket, "Failed to join room", message.request_id)
            return False


class ReJoinRoomHandler(BaseHandler):
    """Handles room rejoining requests."""
    
    async def handle(self, websocket: websockets.ServerConnection, message: ReJoinRoomClientMessage) -> bool:
        try:
            room_id = message.room
            user_id = message.user
            
            # Try to rejoin room through game gateway
            ret_join = self.game_gateway.rejoin_room(room_id, user_id)
            
            if ret_join == JoinReturnCodes.SUCCESS:
                # Register user connection
                await self.connection_manager.register_user(websocket, room_id, user_id)
                
                # Send success response
                rejoin_ok_msg = ReJoinRoomSuccessServerMessage(
                    room=room_id, 
                    user=user_id, 
                    response_to_request_id=message.request_id
                )
                await self.connection_manager.safe_websocket_send(websocket, rejoin_ok_msg.model_dump_json())
                
                # Small delay to ensure message ordering
                time.sleep(0.1)
                
                # Notify all users in room
                await self.notify_room_users_updated(room_id)
                
                logging.info(f"User '{user_id}' rejoined room '{room_id}'")
                return True
            elif ret_join == JoinReturnCodes.ROOM_NOT_FOUND:
                room_not_found = RoomNotFoundServerMessage()
                await self.connection_manager.safe_websocket_send(websocket, room_not_found.model_dump_json())
                return False
            else:
                await self.send_error(websocket, ret_join, message.request_id)
                return False
                
        except Exception as e:
            logging.error(f"Error rejoining room '{message.room}' for user '{message.user}': {e}")
            await self.send_generic_error(websocket, "Failed to rejoin room", message.request_id)
            return False