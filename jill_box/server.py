#!/usr/bin/env python

import asyncio
import json
import logging
import time
from collections import defaultdict
from typing import Dict, Any, Optional
import websockets
from pydantic import ValidationError, TypeAdapter, ConfigDict
import uuid

# Assuming contracts.py is in the same directory or PYTHONPATH
from jill_box.contracts import (
    IncomingMessage, OutgoingMessage, # Base Union types
    # Specific client message types (for isinstance checks or direct construction if needed)
    CreateRoomClientMessage, JoinRoomClientMessage, StartRoomClientMessage,
    SubmitAnswerClientMessage, SubmitVoteClientMessage,
    # Specific server message types (for construction)
    ErrorServerMessage, JoinRoomSuccessServerMessage, UserUpdateServerMessage,
    AskPromptServerMessage, AskVoteServerMessage, ShowResultsServerMessage,
    GameDoneServerMessage, AnswerOptionForVote, ResultDetail
)

from jill_box.contracts import parse_incoming_message


from jill_box.game import GameGateway, PromptRoom, StartReturnCodes, InteractReturnCodes, JoinReturnCodes, State
GATEWAY = GameGateway()
# GATEWAY = MockGameGateway() # Using the mock for standalone running

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Global state: ROOM_ID -> USER_ID -> WebSocket
USERS: Dict[str, Dict[str, websockets.ServerConnection]] = defaultdict(dict)
# Map WebSocket back to user details for quick lookup on disconnect
WEBSOCKET_TO_USER_INFO: Dict[websockets.ServerConnection, Dict[str, str]] = {}


async def send_typed_error_message(websocket: websockets.ServerConnection, error_code_enum_member, request_id: Optional[str] = None):
    """Sends a Pydantic ErrorServerMessage using the enum member's name."""
    error_msg = ErrorServerMessage(message=error_code_enum_member.name, response_to_request_id=request_id)
    try:
        await websocket.send(error_msg.model_dump_json())
    except websockets.exceptions.ConnectionClosed:
        logging.warning(f"Failed to send error to a closing connection: {websocket.remote_address}")

async def safe_websocket_send(websocket: websockets.ServerConnection, message_json: str):
    """Safely sends a JSON message, raising ConnectionClosed on failure."""
    try:
        await websocket.send(message_json)
    except websockets.exceptions.ConnectionClosed as e:
        logging.debug(f"Connection closed for {websocket.remote_address} during send attempt.")
        raise e # Re-raise for the caller (e.g., broadcast_to_room) to handle

async def broadcast_to_room(room_id: str, message: OutgoingMessage):
    """Broadcasts a Pydantic message to all users in a specific room."""
    if room_id not in USERS:
        logging.warning(f"Attempted to broadcast to non-existent or empty room: {room_id}")
        return

    message_json = message.model_dump_json()
    # Create a list of (user_id, websocket) pairs for robust iteration
    current_connections = list(USERS.get(room_id, {}).items())
    
    if not current_connections:
        logging.info(f"No active connections in room {room_id} to broadcast to.")
        return

    logging.info(f"Broadcasting to room '{room_id}' (Users: {len(current_connections)}): {message.type}")

    tasks = [
        safe_websocket_send(ws, message_json)
        for _, ws in current_connections
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            user_id, ws = current_connections[i]
            logging.warning(f"Broadcast to user '{user_id}' in room '{room_id}' failed ({ws.remote_address}): {type(result).__name__}. User will be cleaned up if connection is fully closed.")
            # The main message_handler's finally block will call unregister_user for failed connections.

async def notify_users_of_room_update(room_id: str):
    """Sends UserUpdateServerMessage to all users in the room."""
    if room_id in USERS and USERS[room_id]:
        current_users_in_room = list(USERS[room_id].keys())
        update_msg = UserUpdateServerMessage(users=current_users_in_room)
        await broadcast_to_room(room_id, update_msg)

async def unregister_user(websocket: websockets.ServerConnection):
    """Removes a user from global tracking and notifies others in their room."""
    user_info = WEBSOCKET_TO_USER_INFO.pop(websocket, None)
    if user_info:
        room_id = user_info["room_id"]
        user_id = user_info["user_id"]
        logging.info(f"Unregistering user '{user_id}' from room '{room_id}' ({websocket.remote_address}).")
        if room_id in USERS and user_id in USERS[room_id]:
            del USERS[room_id][user_id]
            if not USERS[room_id]: # Room is empty
                del USERS[room_id]
                logging.info(f"Removed empty room '{room_id}'.")
            else:
                # Notify remaining users about the disconnection
                await notify_users_of_room_update(room_id)
        else:
            logging.warning(f"User '{user_id}' or room '{room_id}' partially cleaned up or not found in USERS during unregister.")
    else:
        logging.debug(f"Websocket {websocket.remote_address} not found in WEBSOCKET_TO_USER_INFO during unregister (already cleaned up or never fully registered).")

async def handle_ask_prompt_for_room(room_id: str):
    _, _, prompt_json = GATEWAY.get_room_state(room_id)
    try:
        prompt_text = prompt_json
        if isinstance(prompt_text, str):
            prompt_msg = AskPromptServerMessage(prompt=prompt_text)
            await broadcast_to_room(room_id, prompt_msg)
        else:
            logging.error(f"Unexpected prompt format for room '{room_id}': {prompt_text}")
    except json.JSONDecodeError:
        logging.error(f"Failed to decode prompt JSON for room '{room_id}': {prompt_json}")

async def handle_ask_vote_for_room(room_id: str):
    if room_id not in USERS: return

    active_connections = list(USERS[room_id].items())
    tasks = []
    for user_id, ws in active_connections:
        _, _, answers_json = GATEWAY.get_room_state(room_id, user_id) # Pass user_id for filtering
        try:
            answers_list_of_dicts = json.loads(answers_json)
            print(answers_list_of_dicts)
            valid_answers = [AnswerOptionForVote(**ans) for ans in answers_list_of_dicts['answers']]
            vote_msg = AskVoteServerMessage(prompt=answers_list_of_dicts['prompt'], answers=valid_answers)
            # Send individually as content might be user-specific
            tasks.append(safe_websocket_send(ws, vote_msg.model_dump_json()))
        except (json.JSONDecodeError, ValidationError) as e:
            logging.error(f"Error preparing vote message for user '{user_id}' in room '{room_id}' with data \n---{answers_json}\n---: {e}")
            # Optionally send an error to this specific user
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def handle_show_results_for_room(room_id: str):
    _, _, results_json = GATEWAY.get_room_state(room_id)
    try:
        results_list_of_dicts = json.loads(results_json)
        print(results_list_of_dicts)
        valid_results = [ResultDetail(**res) for res in results_list_of_dicts]
        results_msg = ShowResultsServerMessage(results=valid_results)
        await broadcast_to_room(room_id, results_msg)
    except (json.JSONDecodeError, ValidationError) as e:
        logging.error(f"Error preparing results message for room '{room_id}' with json ---\n{results_list_of_dicts}\n---: {e}")

async def handle_next_round_logic(room_id: str):
    """Server-initiated logic to advance the game round or end the game."""
    if room_id not in USERS or not USERS[room_id]:
        logging.info(f"Skipping next round logic for empty or non-existent room '{room_id}'.")
        return

    # Use an arbitrary user from the room to trigger the state change in the gateway
    # This call to submit_data with empty dict advances the game state internally in GATEWAY
    first_user_id_in_room = next(iter(USERS[room_id]))
    GATEWAY.submit_data(room_id, first_user_id_in_room, {})

    # After advancing, get the new state and send appropriate messages
    _, state_val, _ = GATEWAY.get_room_state(room_id) # We don't need the data payload here
    current_game_state = State(state_val) if state_val is not None else None # Reconstruct enum from value
    
    logging.info(f"Room '{room_id}' advanced: New Gateway state is {current_game_state.name if current_game_state else 'UNKNOWN'}")

    if current_game_state == State.COLLECTING_ANSWERS:
        await asyncio.sleep(1) # Small delay, original had 20s
        await handle_ask_prompt_for_room(room_id)
    elif current_game_state == State.DONE:
        done_msg = GameDoneServerMessage() # Default message is in the model
        await broadcast_to_room(room_id, done_msg)
    else:
        logging.warning(f"Room '{room_id}' in unexpected state {current_game_state.name if current_game_state else 'UNKNOWN'} after trying to start next round.")

async def message_handler(websocket: websockets.ServerConnection):
    """Main handler for individual websocket connections."""
    # logging.info(f"Client connected: {websocket.remote_address} on path {path}")
    try:
        async for message_str in websocket:
            request_id_for_response: Optional[str] = None
            try:
                # parsed_message: IncomingMessage = IncomingMessage.model_validate_json(data)
                parsed_message = parse_incoming_message(str(message_str))
                request_id_for_response = parsed_message.request_id
                logging.info(f"Received '{parsed_message.type}' from {websocket.remote_address}")

                current_room_id: Optional[str] = WEBSOCKET_TO_USER_INFO.get(websocket, {}).get("room_id")
                current_user_id: Optional[str] = WEBSOCKET_TO_USER_INFO.get(websocket, {}).get("user_id")

                if isinstance(parsed_message, CreateRoomClientMessage):
                    room_id = GATEWAY.new_game(PromptRoom) # TestRoom is a placeholder type
                    user_id = parsed_message.user
                    
                    ret_join = GATEWAY.join_room(room_id, user_id)
                    if ret_join == JoinReturnCodes.SUCCESS:
                        USERS[room_id][user_id] = websocket
                        WEBSOCKET_TO_USER_INFO[websocket] = {"room_id": room_id, "user_id": user_id}
                        join_ok_msg = JoinRoomSuccessServerMessage(room=room_id, user=user_id, response_to_request_id=request_id_for_response)
                        await safe_websocket_send(websocket, join_ok_msg.model_dump_json())
                        await notify_users_of_room_update(room_id)
                    else:
                        await send_typed_error_message(websocket, ret_join, request_id_for_response)

                elif isinstance(parsed_message, JoinRoomClientMessage):
                    room_id = parsed_message.room
                    user_id = parsed_message.user
                    ret_join = GATEWAY.join_room(room_id, user_id)
                    if ret_join == JoinReturnCodes.SUCCESS:
                        USERS[room_id][user_id] = websocket
                        WEBSOCKET_TO_USER_INFO[websocket] = {"room_id": room_id, "user_id": user_id}
                        join_ok_msg = JoinRoomSuccessServerMessage(room=room_id, user=user_id, response_to_request_id=request_id_for_response)
                        await safe_websocket_send(websocket, join_ok_msg.model_dump_json())
                        
                        # gross solution
                        # Sending the ok join socket and the user update socket need to be delayed so that they get recieved in the correct
                        # order. Either need to combine the data messages.
                        time.sleep(0.1) 
                        await notify_users_of_room_update(room_id)
                    else:
                        await send_typed_error_message(websocket, ret_join, request_id_for_response)
                
                # For actions requiring user to be in a room and authenticated:
                elif current_room_id and current_user_id:
                    if isinstance(parsed_message, StartRoomClientMessage):
                        if parsed_message.room == current_room_id: # Ensure action is for their current room
                            ret_start = GATEWAY.room_start(current_room_id)
                            if ret_start == StartReturnCodes.SUCCESS:
                                await handle_ask_prompt_for_room(current_room_id)
                            else:
                                await send_typed_error_message(websocket, ret_start, request_id_for_response)
                        else: # Security: User tried to start a room they are not in.
                            logging.warning(f"User '{current_user_id}' tried to start room '{parsed_message.room}' but is in '{current_room_id}'.")
                            await send_typed_error_message(websocket, InteractReturnCodes.INVALID_DATA, request_id_for_response)


                    elif isinstance(parsed_message, SubmitAnswerClientMessage) or isinstance(parsed_message, SubmitVoteClientMessage):
                        # Ensure message's room and user match connection's context
                        if parsed_message.room == current_room_id and parsed_message.user == current_user_id:
                            ret_submit = GATEWAY.submit_data(current_room_id, current_user_id, parsed_message.model_dump())
                            if ret_submit == InteractReturnCodes.SUCCESS:
                                _, state_val, _ = GATEWAY.get_room_state(current_room_id)
                                current_game_state = State(state_val) if state_val is not None else None
                                logging.info(f"Room '{current_room_id}' state after submit by '{current_user_id}': {current_game_state.name if current_game_state else 'UNKNOWN'}")

                                if isinstance(parsed_message, SubmitAnswerClientMessage) and current_game_state == State.VOTING:
                                    await handle_ask_vote_for_room(current_room_id)
                                elif isinstance(parsed_message, SubmitVoteClientMessage) and current_game_state == State.SHOWING_RESULTS:
                                    await handle_show_results_for_room(current_room_id)
                                    asyncio.create_task(handle_next_round_logic(current_room_id))
                            else:
                                await send_typed_error_message(websocket, ret_submit, request_id_for_response)
                        else:
                            logging.warning(f"Mismatch in submit: msg_room='{parsed_message.room}', msg_user='{parsed_message.user}' vs ws_room='{current_room_id}', ws_user='{current_user_id}'.")
                            await send_typed_error_message(websocket, InteractReturnCodes.INVALID_DATA, request_id_for_response)
                else: # Client sent a message type that requires being in a room, but they are not.
                    if parsed_message.type not in ["create_room", "join_room"]:
                         logging.warning(f"User {websocket.remote_address} sent '{parsed_message.type}' but is not registered in a room.")
                         error_msg = ErrorServerMessage(message="Action requires being in a room. Please join or create a room.", response_to_request_id=request_id_for_response)
                         await safe_websocket_send(websocket, error_msg.model_dump_json())


            except ValidationError as e:
                logging.error(f"Pydantic Validation Error from {websocket.remote_address}: {e.errors()}")
                error_response = ErrorServerMessage(message="Invalid message format or data.", response_to_request_id=request_id_for_response)
                await safe_websocket_send(websocket, error_response.model_dump_json())
            except json.JSONDecodeError:
                logging.error(f"Received invalid JSON from {websocket.remote_address}: {message_str[:200]}") # Log snippet
                error_response = ErrorServerMessage(message="Invalid JSON format.", response_to_request_id=request_id_for_response) # request_id might not be parsable here
                await safe_websocket_send(websocket, error_response.model_dump_json())
            except websockets.exceptions.ConnectionClosed: # Catch if safe_websocket_send re-raises during error response
                raise # Re-raise to be handled by outer finally
            except Exception as e: # Catch-all for other errors during message processing
                logging.error(f"Received invalid JSON from {websocket.remote_address}: {message_str[:200]}") # Log snippet
                logging.exception(f"Unexpected error processing message from {websocket.remote_address}: {e}")
                error_response = ErrorServerMessage(message="Internal server error.", response_to_request_id=request_id_for_response)
                try: # Try to send final error, but connection might be gone
                    await safe_websocket_send(websocket, error_response.model_dump_json())
                except websockets.exceptions.ConnectionClosed:
                    pass # Will be handled by outer finally

    except websockets.exceptions.ConnectionClosedOK:
        logging.info(f"Client disconnected gracefully: {websocket.remote_address}")
    except websockets.exceptions.ConnectionClosedError as e:
        logging.warning(f"Client connection closed with error: {websocket.remote_address}, Error: {e}")
    except Exception as e: # Catch-all for unexpected errors in the connection loop itself
        logging.exception(f"Unexpected error in connection handler for {websocket.remote_address}: {e}")
    finally:
        await unregister_user(websocket)
        logging.info(f"Client connection closed and cleaned up: {websocket.remote_address}")


async def main():
    server_address = "0.0.0.0"
    server_port = 6969
    logging.info(f"Starting WebSocket server on ws://{server_address}:{server_port}")
    async with websockets.serve(message_handler, server_address, server_port):
        await asyncio.Future()  # Run forever

asyncio.run(main())