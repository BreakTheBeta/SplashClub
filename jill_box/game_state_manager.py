# game_state_manager.py

import json
import logging
import asyncio
from typing import List
from pydantic import ValidationError
from jill_box.contracts import (
    AskPromptServerMessage, AskVoteServerMessage, ShowResultsServerMessage,
    GameDoneServerMessage, AnswerOptionForVote, ResultDetail
)
from jill_box.game import State
from jill_box.connection_manager import ConnectionManager
from jill_box.game import GameGateway


class GameStateManager:
    """Manages game state transitions and sends appropriate messages to players."""
    
    def __init__(self, connection_manager: ConnectionManager, game_gateway: GameGateway):
        self.connection_manager = connection_manager
        self.game_gateway = game_gateway
        
    async def handle_ask_prompt_for_room(self, room_id: str) -> None:
        """Send prompt message to all users in the room."""
        try:
            game_state = self.game_gateway.get_room_state(room_id)
            if not game_state:
                logging.error(f"Could not get room state for room '{room_id}'")
                return
                
            _, _, prompt_json = game_state
            
            if isinstance(prompt_json, str):
                prompt_msg = AskPromptServerMessage(prompt=prompt_json)
                await self.connection_manager.broadcast_to_room(room_id, prompt_msg)
                logging.info(f"Sent prompt to room '{room_id}': {prompt_json[:50]}...")
            else:
                logging.error(f"Unexpected prompt format for room '{room_id}': {type(prompt_json)}")
                
        except Exception as e:
            logging.error(f"Error handling prompt for room '{room_id}': {e}")
            
    async def handle_ask_vote_for_room(self, room_id: str) -> None:
        """Send voting options to all users in the room."""
        if not self.connection_manager.room_exists(room_id):
            logging.warning(f"Attempted to handle vote for non-existent room: {room_id}")
            return
            
        try:
            # Get current connections to avoid modification during iteration
            user_connections = list(self.connection_manager.users[room_id].items())
            
            tasks = []
            for user_id, websocket in user_connections:
                try:
                    # Get user-specific game state (filters answers appropriately)
                    game_state = self.game_gateway.get_room_state(room_id, user_id)
                    if not game_state:
                        logging.error(f"Could not get room state for user '{user_id}' in room '{room_id}'")
                        continue
                        
                    _, _, game_data = game_state
                    
                    # Parse answers for voting
                    answers_data = game_data.get('answers', [])
                    prompt_text = game_data.get('prompt', '')
                    
                    valid_answers = [AnswerOptionForVote(**ans) for ans in answers_data]
                    vote_msg = AskVoteServerMessage(prompt=prompt_text, answers=valid_answers)
                    
                    # Send to individual user (content might be user-specific)
                    tasks.append(self.connection_manager.safe_websocket_send(websocket, vote_msg.model_dump_json()))
                    
                except (KeyError, ValidationError) as e:
                    logging.error(f"Error preparing vote message for user '{user_id}' in room '{room_id}': {e}")
                    continue
                    
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                successful_sends = sum(1 for result in results if result is True)
                logging.info(f"Sent vote options to {successful_sends}/{len(tasks)} users in room '{room_id}'")
            else:
                logging.warning(f"No valid vote messages prepared for room '{room_id}'")
                
        except Exception as e:
            logging.error(f"Error handling vote for room '{room_id}': {e}")
            
    async def handle_show_results_for_room(self, room_id: str) -> None:
        """Send game results to all users in the room."""
        try:
            game_state = self.game_gateway.get_room_state(room_id)
            if not game_state:
                logging.error(f"Could not get room state for room '{room_id}'")
                return
                
            _, _, game_data = game_state
            
            # Parse results data
            if isinstance(game_data, list):
                results_data = game_data
            elif isinstance(game_data, dict) and 'results' in game_data:
                results_data = game_data['results']
            else:
                logging.error(f"Unexpected results format for room '{room_id}': {type(game_data)}")
                return
                
            valid_results = [ResultDetail(**res) for res in results_data]
            results_msg = ShowResultsServerMessage(results=valid_results)
            
            await self.connection_manager.broadcast_to_room(room_id, results_msg)
            logging.info(f"Sent results to room '{room_id}' ({len(valid_results)} results)")
            
        except (ValidationError, KeyError) as e:
            logging.error(f"Error preparing results for room '{room_id}': {e}")
        except Exception as e:
            logging.error(f"Error handling results for room '{room_id}': {e}")
            
    async def handle_next_round_logic(self, room_id: str) -> None:
        """Advance the game to the next round or end the game."""
        try:
            if not self.connection_manager.room_exists(room_id):
                logging.info(f"Skipping next round logic for non-existent room '{room_id}'")
                return
                
            # Get any user from the room to trigger state advancement
            room_users = self.connection_manager.get_room_users(room_id)
            if not room_users:
                logging.info(f"No users in room '{room_id}' for next round")
                return
                
            first_user = room_users[0]
            
            # Advance game state (empty dict triggers state change)
            self.game_gateway.submit_data(room_id, first_user, {})
            
            # Check new state and respond accordingly
            game_state = self.game_gateway.get_room_state(room_id)
            if not game_state:
                logging.error(f"Could not get room state after advancing room '{room_id}'")
                return
                
            _, state_val, _ = game_state
            current_game_state = State(state_val) if state_val is not None else None
            
            logging.info(f"Room '{room_id}' advanced to state: {current_game_state.name if current_game_state else 'UNKNOWN'}")
            
            if current_game_state == State.COLLECTING_ANSWERS:
                # Small delay before asking for next prompt
                await asyncio.sleep(1)
                await self.handle_ask_prompt_for_room(room_id)
                
            elif current_game_state == State.DONE:
                done_msg = GameDoneServerMessage()
                await self.connection_manager.broadcast_to_room(room_id, done_msg)
                logging.info(f"Game completed for room '{room_id}'")
                
            else:
                logging.warning(f"Room '{room_id}' in unexpected state after next round: {current_game_state.name if current_game_state else 'UNKNOWN'}")
                
        except Exception as e:
            logging.error(f"Error in next round logic for room '{room_id}': {e}")