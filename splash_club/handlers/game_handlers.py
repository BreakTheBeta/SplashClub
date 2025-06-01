# handlers/game_handlers.py

import logging
import asyncio
import websockets
from .base_handler import BaseHandler
from splash_club.contracts import (
    StartRoomClientMessage, SubmitAnswerClientMessage, SubmitVoteClientMessage, IncomingMessage
)
from splash_club.game import StartReturnCodes, InteractReturnCodes, State
from splash_club.game_state_manager import GameStateManager


class StartRoomHandler(BaseHandler):
    """Handles room start requests."""
    
    async def handle(self, websocket: websockets.ServerConnection, message: StartRoomClientMessage) -> bool:
        try:
            user_info = self.get_user_context(websocket)
            
            if not user_info:
                await self.send_generic_error(websocket, "Must be in a room to start game", message.request_id)
                return False
                
            current_room_id = user_info.get("room_id")
            current_user_id = user_info.get("user_id")
            
            if not current_room_id or not current_user_id:
                await self.send_generic_error(websocket, "Must be in a room to start game", message.request_id)
                return False
                
            # Security check: ensure user is trying to start their current room
            if message.room != current_room_id:
                logging.warning(f"User '{current_user_id}' tried to start room '{message.room}' but is in '{current_room_id}'")
                await self.send_error(websocket, InteractReturnCodes.INVALID_DATA, message.request_id)
                return False
                
            # Try to start the room
            ret_start = self.game_gateway.room_start(current_room_id)
            
            if ret_start == StartReturnCodes.SUCCESS:
                # Import here to avoid circular imports
                from ..game_state_manager import GameStateManager
                game_state_manager = GameStateManager(self.connection_manager, self.game_gateway)
                await game_state_manager.handle_ask_prompt_for_room(current_room_id)
                
                logging.info(f"Room '{current_room_id}' started by user '{current_user_id}'")
                return True
            else:
                await self.send_error(websocket, ret_start, message.request_id)
                return False
                
        except Exception as e:
            logging.error(f"Error starting room: {e}")
            await self.send_generic_error(websocket, "Failed to start room", message.request_id)
            return False


class SubmitAnswerHandler(BaseHandler):
    """Handles answer submission requests."""
    
    async def handle(self, websocket: websockets.ServerConnection, message: SubmitAnswerClientMessage) -> bool:
        try:
            user_info = self.get_user_context(websocket)
            
            if not user_info:
                await self.send_generic_error(websocket, "Must be in a room to submit answer", message.request_id)
                return False
                
            current_room_id = user_info.get("room_id")
            current_user_id = user_info.get("user_id")
            
            if not current_room_id or not current_user_id:
                await self.send_generic_error(websocket, "Must be in a room to submit answer", message.request_id)
                return False
                
            # Security check: ensure message context matches connection context
            if message.room != current_room_id or message.user != current_user_id:
                logging.warning(f"Submit mismatch: msg_room='{message.room}', msg_user='{message.user}' vs ws_room='{current_room_id}', ws_user='{current_user_id}'")
                await self.send_error(websocket, InteractReturnCodes.INVALID_DATA, message.request_id)
                return False
                
            # Submit answer to game
            ret_submit = self.game_gateway.submit_data(current_room_id, current_user_id, message.model_dump())
            
            if ret_submit == InteractReturnCodes.SUCCESS:
                # Check new game state
                _, state_val, _ = self.game_gateway.get_room_state(current_room_id)
                current_game_state = State(state_val) if state_val is not None else None
                
                logging.info(f"Room '{current_room_id}' state after answer submit by '{current_user_id}': {current_game_state.name if current_game_state else 'UNKNOWN'}")
                
                # If all answers collected, move to voting
                if current_game_state == State.VOTING:
                    from ..game_state_manager import GameStateManager
                    game_state_manager = GameStateManager(self.connection_manager, self.game_gateway)
                    await game_state_manager.handle_ask_vote_for_room(current_room_id)
                    
                return True
            else:
                await self.send_error(websocket, ret_submit, message.request_id)
                return False
                
        except Exception as e:
            logging.error(f"Error submitting answer: {e}")
            await self.send_generic_error(websocket, "Failed to submit answer", message.request_id)
            return False


class SubmitVoteHandler(BaseHandler):
    """Handles vote submission requests."""
    
    async def handle(self, websocket: websockets.ServerConnection, message: SubmitVoteClientMessage) -> bool:
        try:
            user_info = self.get_user_context(websocket)
            
            if not user_info:
                await self.send_generic_error(websocket, "Must be in a room to submit vote", message.request_id)
                return False
                
            current_room_id = user_info.get("room_id")
            current_user_id = user_info.get("user_id")
            
            if not current_room_id or not current_user_id:
                await self.send_generic_error(websocket, "Must be in a room to submit vote", message.request_id)
                return False
                
            # Security check: ensure message context matches connection context
            if message.room != current_room_id or message.user != current_user_id:
                logging.warning(f"Vote submit mismatch: msg_room='{message.room}', msg_user='{message.user}' vs ws_room='{current_room_id}', ws_user='{current_user_id}'")
                await self.send_error(websocket, InteractReturnCodes.INVALID_DATA, message.request_id)
                return False
                
            # Submit vote to game
            ret_submit = self.game_gateway.submit_data(current_room_id, current_user_id, message.model_dump())
            
            if ret_submit == InteractReturnCodes.SUCCESS:
                # Check new game state
                _, state_val, _ = self.game_gateway.get_room_state(current_room_id)
                current_game_state = State(state_val) if state_val is not None else None
                
                logging.info(f"Room '{current_room_id}' state after vote submit by '{current_user_id}': {current_game_state.name if current_game_state else 'UNKNOWN'}")
                
                # If all votes collected, show results and prepare next round
                if current_game_state == State.SHOWING_RESULTS:
                    from ..game_state_manager import GameStateManager
                    game_state_manager = GameStateManager(self.connection_manager, self.game_gateway)
                    await game_state_manager.handle_show_results_for_room(current_room_id)
                    
                    logging.info(f"Starting next round for room '{current_room_id}'")
                    # Start next round logic asynchronously
                    asyncio.create_task(game_state_manager.handle_next_round_logic(current_room_id))
                    
                return True
            else:
                await self.send_error(websocket, ret_submit, message.request_id)
                return False
                
        except Exception as e:
            logging.error(f"Error submitting vote: {e}")
            await self.send_generic_error(websocket, "Failed to submit vote", message.request_id)
            return False