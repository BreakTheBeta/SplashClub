# handlers/room_handlers.py

import time
import logging
import websockets
from .base_handler import BaseHandler
from splash_club.contracts import (
    CreateRoomClientMessage, JoinRoomClientMessage, ReJoinRoomClientMessage,
    JoinRoomSuccessServerMessage, ReJoinRoomSuccessServerMessage, RoomNotFoundServerMessage,
    AskPromptServerMessage, AskVoteServerMessage, ShowResultsServerMessage, AnswerOptionForVote, ResultDetail
)
from splash_club.game import PromptRoom, JoinReturnCodes, State, InteractReturnCodes
from splash_club.connection_manager import ConnectionManager
from pydantic import ValidationError


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
                
                # NEW: Send game state synchronization messages
                await self._send_game_state_sync(websocket, room_id, user_id)
                
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
    
    async def _send_game_state_sync(self, websocket: websockets.ServerConnection, room_id: str, user_id: str) -> None:
        """Send appropriate game state messages to sync the rejoining client."""
        try:
            # Get current game state
            game_state = self.game_gateway.get_room_state(room_id, user_id)
            if not game_state:
                logging.error(f"Could not get room state for user '{user_id}' in room '{room_id}' during rejoin sync")
                return
                
            ret_code, state_val, game_data = game_state
            
            if ret_code != InteractReturnCodes.SUCCESS:
                logging.error(f"Failed to get room state for user '{user_id}' in room '{room_id}': {ret_code}")
                return
                
            current_state = State(state_val) if state_val is not None else None
            
            if current_state == State.WAITING_TO_START:
                # Client will stay on waiting page, no additional message needed
                logging.info(f"User '{user_id}' rejoined room '{room_id}' in WAITING_TO_START state")
                
            elif current_state == State.COLLECTING_ANSWERS:
                # Send prompt message to get client to prompt page
                if isinstance(game_data, str):
                    prompt_msg = AskPromptServerMessage(prompt=game_data)
                    await self.connection_manager.safe_websocket_send(websocket, prompt_msg.model_dump_json())
                    logging.info(f"Sent prompt sync to rejoining user '{user_id}' in room '{room_id}'")
                else:
                    logging.error(f"Unexpected prompt format for room '{room_id}' during rejoin: {type(game_data)}")
                    
            elif current_state == State.VOTING:
                # Send voting options to get client to vote page
                if isinstance(game_data, dict) and 'prompt' in game_data and 'answers' in game_data:
                    try:
                        answers_data = game_data.get('answers', [])
                        prompt_text = game_data.get('prompt', '')
                        
                        valid_answers = [AnswerOptionForVote(**ans) for ans in answers_data]
                        vote_msg = AskVoteServerMessage(prompt=prompt_text, answers=valid_answers)
                        
                        await self.connection_manager.safe_websocket_send(websocket, vote_msg.model_dump_json())
                        logging.info(f"Sent vote sync to rejoining user '{user_id}' in room '{room_id}'")
                        
                    except (KeyError, ValidationError) as e:
                        logging.error(f"Error preparing vote sync message for user '{user_id}' in room '{room_id}': {e}")
                else:
                    logging.error(f"Unexpected vote data format for room '{room_id}' during rejoin: {type(game_data)}")
                    
            elif current_state == State.SHOWING_RESULTS:
                # Send results to get client to results page
                if isinstance(game_data, list):
                    try:
                        valid_results = [ResultDetail(**res) for res in game_data]
                        results_msg = ShowResultsServerMessage(results=valid_results)
                        
                        await self.connection_manager.safe_websocket_send(websocket, results_msg.model_dump_json())
                        logging.info(f"Sent results sync to rejoining user '{user_id}' in room '{room_id}'")
                        
                    except (ValidationError, KeyError) as e:
                        logging.error(f"Error preparing results sync message for user '{user_id}' in room '{room_id}': {e}")
                else:
                    logging.error(f"Unexpected results format for room '{room_id}' during rejoin: {type(game_data)}")
                    
            elif current_state == State.DONE:
                # Game is over, client will stay on waiting/results page
                logging.info(f"User '{user_id}' rejoined room '{room_id}' in DONE state")
                
            else:
                logging.warning(f"Unknown game state '{current_state}' for room '{room_id}' during rejoin sync")
                
        except Exception as e:
            logging.error(f"Error sending game state sync for user '{user_id}' in room '{room_id}': {e}")