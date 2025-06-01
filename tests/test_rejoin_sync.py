#!/usr/bin/env python3

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import json

from splash_club.handlers.room_handlers import ReJoinRoomHandler
from splash_club.game import GameGateway, PromptRoom, State, InteractReturnCodes, JoinReturnCodes
from splash_club.connection_manager import ConnectionManager
from splash_club.contracts import ReJoinRoomClientMessage


class TestRejoinGameStateSync:
    """Test suite for rejoin game state synchronization functionality."""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock websocket."""
        websocket = AsyncMock()
        websocket.send = AsyncMock()
        return websocket
    
    @pytest.fixture
    def game_gateway(self):
        """Create a GameGateway instance for testing."""
        return GameGateway()
    
    @pytest.fixture
    def connection_manager(self):
        """Create a mock ConnectionManager."""
        manager = MagicMock(spec=ConnectionManager)
        manager.register_user = AsyncMock()
        manager.safe_websocket_send = AsyncMock(return_value=True)
        return manager
    
    @pytest.fixture
    def rejoin_handler(self, connection_manager, game_gateway):
        """Create a ReJoinRoomHandler instance."""
        handler = ReJoinRoomHandler(connection_manager, game_gateway)
        handler.notify_room_users_updated = AsyncMock()
        return handler
    
    @pytest.fixture
    def room_with_game_in_progress(self, game_gateway):
        """Create a room with a game in progress in different states."""
        room_id = game_gateway.new_game(PromptRoom)
        
        # Add players
        game_gateway.join_room(room_id, "alice")
        game_gateway.join_room(room_id, "bob") 
        game_gateway.join_room(room_id, "charlie")
        
        return room_id, game_gateway.rooms[room_id]
    
    @pytest.mark.asyncio
    async def test_rejoin_waiting_to_start_state(self, rejoin_handler, mock_websocket, room_with_game_in_progress):
        """Test rejoining when game is in WAITING_TO_START state."""
        room_id, room = room_with_game_in_progress
        
        # Game is in WAITING_TO_START by default
        assert room.state == State.WAITING_TO_START
        
        message = ReJoinRoomClientMessage(room=room_id, user="alice")
        
        result = await rejoin_handler.handle(mock_websocket, message)
        
        assert result is True
        rejoin_handler.connection_manager.register_user.assert_called_once()
        rejoin_handler.connection_manager.safe_websocket_send.assert_called()
        
        # Should send rejoin_room_ok but no additional game state messages for WAITING_TO_START
        calls = rejoin_handler.connection_manager.safe_websocket_send.call_args_list
        assert len(calls) == 1  # Only rejoin_room_ok message
        
        sent_message = json.loads(calls[0][0][1])
        assert sent_message["type"] == "rejoin_room_ok"
    
    @pytest.mark.asyncio
    async def test_rejoin_collecting_answers_state(self, rejoin_handler, mock_websocket, room_with_game_in_progress):
        """Test rejoining when game is in COLLECTING_ANSWERS state."""
        room_id, room = room_with_game_in_progress
        
        # Start the game to move to COLLECTING_ANSWERS
        room.start()
        assert room.state == State.COLLECTING_ANSWERS
        
        message = ReJoinRoomClientMessage(room=room_id, user="alice")
        
        result = await rejoin_handler.handle(mock_websocket, message)
        
        assert result is True
        
        # Should send rejoin_room_ok + ask_prompt messages
        calls = rejoin_handler.connection_manager.safe_websocket_send.call_args_list
        assert len(calls) == 2
        
        # First message should be rejoin_room_ok
        rejoin_message = json.loads(calls[0][0][1])
        assert rejoin_message["type"] == "rejoin_room_ok"
        
        # Second message should be ask_prompt
        prompt_message = json.loads(calls[1][0][1])
        assert prompt_message["type"] == "ask_prompt"
        assert "prompt" in prompt_message
    
    @pytest.mark.asyncio
    async def test_rejoin_voting_state(self, rejoin_handler, mock_websocket, room_with_game_in_progress):
        """Test rejoining when game is in VOTING state."""
        room_id, room = room_with_game_in_progress
        
        # Start game and submit answers to move to VOTING
        room.start()
        room.submit_data("alice", {"answer": "answer1"})
        room.submit_data("bob", {"answer": "answer2"})
        room.submit_data("charlie", {"answer": "answer3"})
        
        assert room.state == State.VOTING
        
        message = ReJoinRoomClientMessage(room=room_id, user="alice")
        
        result = await rejoin_handler.handle(mock_websocket, message)
        
        assert result is True
        
        # Should send rejoin_room_ok + ask_vote messages
        calls = rejoin_handler.connection_manager.safe_websocket_send.call_args_list
        assert len(calls) == 2
        
        # First message should be rejoin_room_ok
        rejoin_message = json.loads(calls[0][0][1])
        assert rejoin_message["type"] == "rejoin_room_ok"
        
        # Second message should be ask_vote
        vote_message = json.loads(calls[1][0][1])
        assert vote_message["type"] == "ask_vote"
        assert "prompt" in vote_message
        assert "answers" in vote_message
        assert isinstance(vote_message["answers"], list)
    
    @pytest.mark.asyncio
    async def test_rejoin_showing_results_state(self, rejoin_handler, mock_websocket, room_with_game_in_progress):
        """Test rejoining when game is in SHOWING_RESULTS state."""
        room_id, room = room_with_game_in_progress
        
        # Start game, submit answers and votes to move to SHOWING_RESULTS
        room.start()
        room.submit_data("alice", {"answer": "answer1"})
        room.submit_data("bob", {"answer": "answer2"})
        room.submit_data("charlie", {"answer": "answer3"})
        
        # Submit votes
        room.submit_data("alice", {"voted_for_answer_id": "bob"})
        room.submit_data("bob", {"voted_for_answer_id": "charlie"})
        room.submit_data("charlie", {"voted_for_answer_id": "alice"})
        
        assert room.state == State.SHOWING_RESULTS
        
        message = ReJoinRoomClientMessage(room=room_id, user="alice")
        
        result = await rejoin_handler.handle(mock_websocket, message)
        
        assert result is True
        
        # Should send rejoin_room_ok + show_results messages
        calls = rejoin_handler.connection_manager.safe_websocket_send.call_args_list
        assert len(calls) == 2
        
        # First message should be rejoin_room_ok
        rejoin_message = json.loads(calls[0][0][1])
        assert rejoin_message["type"] == "rejoin_room_ok"
        
        # Second message should be show_results
        results_message = json.loads(calls[1][0][1])
        assert results_message["type"] == "show_results"
        assert "results" in results_message
        assert isinstance(results_message["results"], list)
    
    @pytest.mark.asyncio
    async def test_rejoin_room_not_found(self, rejoin_handler, mock_websocket):
        """Test rejoining a non-existent room."""
        message = ReJoinRoomClientMessage(room="XXXX", user="alice")
        
        result = await rejoin_handler.handle(mock_websocket, message)
        
        assert result is False
        
        # Should send room_not_found message
        calls = rejoin_handler.connection_manager.safe_websocket_send.call_args_list
        assert len(calls) == 1
        
        sent_message = json.loads(calls[0][0][1])
        assert sent_message["type"] == "room_not_found"
    
    @pytest.mark.asyncio
    async def test_rejoin_player_not_in_room(self, rejoin_handler, mock_websocket, room_with_game_in_progress):
        """Test rejoining with a player that was never in the room."""
        room_id, room = room_with_game_in_progress
        
        # Mock the send_error method on the handler instance
        rejoin_handler.send_error = AsyncMock(return_value=True)
        
        message = ReJoinRoomClientMessage(room=room_id, user="nonexistent")
        
        result = await rejoin_handler.handle(mock_websocket, message)
        
        assert result is False
        
        # Should call send_error method
        rejoin_handler.send_error.assert_called_once()
        
        # Check the arguments passed to send_error
        call_args = rejoin_handler.send_error.call_args
        websocket_arg = call_args[0][0]  # First argument is websocket
        error_code_arg = call_args[0][1]  # Second argument is error code enum
        request_id_arg = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get('request_id')  # Third argument or kwarg
        
        assert websocket_arg == mock_websocket
        assert error_code_arg == JoinReturnCodes.NAME_IN_USE
        assert request_id_arg == message.request_id
    
    @pytest.mark.asyncio
    async def test_sync_handles_exceptions_gracefully(self, rejoin_handler, mock_websocket, room_with_game_in_progress):
        """Test that sync handles exceptions gracefully without breaking rejoin."""
        room_id, room = room_with_game_in_progress
        room.start()
        
        # Mock safe_websocket_send to raise exception on second call (sync message)
        rejoin_handler.connection_manager.safe_websocket_send.side_effect = [True, Exception("Network error")]
        
        message = ReJoinRoomClientMessage(room=room_id, user="alice")
        
        # Should still return True because rejoin succeeded, even if sync failed
        result = await rejoin_handler.handle(mock_websocket, message)
        
        assert result is True
        rejoin_handler.connection_manager.register_user.assert_called_once() 