#!/usr/bin/env python3

import pytest
from unittest.mock import patch, mock_open, MagicMock
import random
import string
from typing import Dict, Any

# Import the classes we're testing
from jill_box.game import (  # Replace 'your_module' with actual module name
    PromptRoom, GameGateway, Player, State, 
    JoinReturnCodes, StartReturnCodes, InteractReturnCodes,
    _random_id, _load_prompts
)


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_random_id_length(self):
        """Test that random_id generates correct length"""
        room_id = _random_id()
        assert len(room_id) == GameGateway.NUM_ROOM_LETTERS
    
    def test_random_id_lowercase(self):
        """Test that random_id only contains lowercase letters"""
        room_id = _random_id()
        assert room_id.islower()
        assert room_id.isalpha()
    
    @patch("builtins.open", new_callable=mock_open, read_data="Question1\tAnswer1\nQuestion2\tAnswer2\n")
    def test_load_prompts(self, mock_file):
        """Test loading prompts from file"""
        prompts = _load_prompts()
        assert len(prompts) == 2
        assert prompts[0] == ("Question1", "Answer1")
        assert prompts[1] == ("Question2", "Answer2")


class TestPlayer:
    """Test Player class"""
    
    def test_player_initialization(self):
        """Test player can be created"""
        player = Player()
        assert isinstance(player, Player)


class TestPromptRoom:
    """Test PromptRoom class"""
    
    @pytest.fixture
    def room(self):
        """Create a PromptRoom instance for testing"""
        with patch.object(PromptRoom, 'PROMPTS', [
            ("What is 2+2?", "4"),
            ("What is the capital of France?", "PARIS"),
            ("What color is the sky?", "BLUE")
        ]):
            return PromptRoom()
    
    @pytest.fixture
    def room_with_players(self, room):
        """Create a room with 3 players added"""
        room.add_player("alice")
        room.add_player("bob")
        room.add_player("charlie")
        return room
    
    def test_room_initialization(self, room):
        """Test room initializes correctly"""
        assert room.state == State.WAITING_TO_START
        assert room.round == 0
        assert len(room.players) == 0
        assert len(room.prompts) == PromptRoom.ROUNDS
        assert isinstance(room.answers, dict)
        assert isinstance(room.votes, dict)
        assert isinstance(room.scores, dict)
    
    def test_add_player_success(self, room):
        """Test adding a new player"""
        result = room.add_player("alice")
        assert result is True
        assert "alice" in room.players
        assert isinstance(room.players["alice"], Player)
    
    def test_add_player_duplicate_name(self, room):
        """Test adding player with existing name fails"""
        room.add_player("alice")
        result = room.add_player("alice")
        assert result is False
        assert len(room.players) == 1
    
    def test_rejoin_player_exists(self, room):
        """Test rejoining existing player"""
        room.add_player("alice")
        result = room.rejoin_player("alice")
        assert result is True
    
    def test_rejoin_player_not_exists(self, room):
        """Test rejoining non-existent player"""
        result = room.rejoin_player("bob")
        assert result is False
    
    def test_start_success(self, room_with_players):
        """Test starting game with enough players"""
        result = room_with_players.start()
        assert result == StartReturnCodes.SUCCESS
        assert room_with_players.state == State.COLLECTING_ANSWERS
        assert len(room_with_players.scores) == 3
        assert all(score == 0 for score in room_with_players.scores.values())
    
    def test_start_too_few_players(self, room):
        """Test starting game with too few players"""
        room.add_player("alice")
        room.add_player("bob")  # Only 2 players, need 3
        result = room.start()
        assert result == StartReturnCodes.TOO_FEW_PLAYERS
        assert room.state == State.WAITING_TO_START
    
    def test_start_already_started(self, room_with_players):
        """Test starting already started game"""
        room_with_players.start()
        result = room_with_players.start()
        assert result == StartReturnCodes.ALREADY_STARTED
    
    def test_get_prompt(self, room):
        """Test getting current prompt"""
        prompt = room.get_prompt()
        assert isinstance(prompt, str)
        assert prompt in [p[0] for p in room.prompts]
    
    def test_submit_answer_collecting_state(self, room_with_players):
        """Test submitting answer during collecting phase"""
        room_with_players.start()
        
        result = room_with_players.submit_data("alice", {"answer": "test answer"})
        assert result == InteractReturnCodes.SUCCESS
        assert "alice" in room_with_players.answers
        assert room_with_players.answers["alice"] == "TEST ANSWER"  # Should be uppercase
    
    def test_submit_answer_invalid_data(self, room_with_players):
        """Test submitting invalid answer data"""
        room_with_players.start()
        
        result = room_with_players.submit_data("alice", {"wrong_key": "test"})
        assert result == InteractReturnCodes.INVALID_DATA
    
    def test_submit_answer_wrong_state(self, room_with_players):
        """Test submitting answer in wrong state"""
        # Don't start the game, should be in WAITING_TO_START
        result = room_with_players.submit_data("alice", {"answer": "test"})
        assert result == InteractReturnCodes.WRONG_STATE
    
    def test_all_answers_submitted_moves_to_voting(self, room_with_players):
        """Test that submitting all answers moves to voting phase"""
        room_with_players.start()
        
        room_with_players.submit_data("alice", {"answer": "answer1"})
        room_with_players.submit_data("bob", {"answer": "answer2"})
        room_with_players.submit_data("charlie", {"answer": "answer3"})
        
        assert room_with_players.state == State.VOTING
        assert PromptRoom.CORRECT_KEY in room_with_players.answers
        assert len(room_with_players.vote_orders) == 3
    
    def test_submit_vote_success(self, room_with_players):
        """Test submitting vote during voting phase"""
        room_with_players.start()
        
        # Submit all answers to move to voting
        room_with_players.submit_data("alice", {"answer": "answer1"})
        room_with_players.submit_data("bob", {"answer": "answer2"})
        room_with_players.submit_data("charlie", {"answer": "answer3"})
        
        # Now submit a vote
        vote_target = room_with_players.vote_orders["alice"][0]
        result = room_with_players.submit_data("alice", {"voted_for_answer_id": vote_target})
        assert result == InteractReturnCodes.SUCCESS
        assert room_with_players.votes["alice"] == vote_target
    
    def test_submit_vote_invalid_data(self, room_with_players):
        """Test submitting invalid vote data"""
        room_with_players.start()
        
        # Move to voting phase
        room_with_players.submit_data("alice", {"answer": "answer1"})
        room_with_players.submit_data("bob", {"answer": "answer2"})
        room_with_players.submit_data("charlie", {"answer": "answer3"})
        
        result = room_with_players.submit_data("alice", {"wrong_key": "vote"})
        assert result == InteractReturnCodes.INVALID_DATA
    
    def test_all_votes_submitted_moves_to_results(self, room_with_players):
        """Test that all votes submitted moves to results phase"""
        room_with_players.start()
        
        # Submit all answers
        room_with_players.submit_data("alice", {"answer": "answer1"})
        room_with_players.submit_data("bob", {"answer": "answer2"})
        room_with_players.submit_data("charlie", {"answer": "answer3"})
        
        # Submit all votes
        room_with_players.submit_data("alice", {"voted_for_answer_id": "bob"})
        room_with_players.submit_data("bob", {"voted_for_answer_id": "charlie"})
        room_with_players.submit_data("charlie", {"voted_for_answer_id": "alice"})
        
        assert room_with_players.state == State.SHOWING_RESULTS
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_results_phase_advances_round(self, mock_sleep, room_with_players):
        """Test that results phase advances to next round"""
        room_with_players.start()
        
        # Complete first round
        room_with_players.submit_data("alice", {"answer": "answer1"})
        room_with_players.submit_data("bob", {"answer": "answer2"})
        room_with_players.submit_data("charlie", {"answer": "answer3"})
        
        room_with_players.submit_data("alice", {"voted_for_answer_id": "bob"})
        room_with_players.submit_data("bob", {"voted_for_answer_id": "charlie"})
        room_with_players.submit_data("charlie", {"voted_for_answer_id": "alice"})
        
        # Submit data during results to advance
        room_with_players.submit_data("alice", {})
        
        assert room_with_players.round == 1
        assert room_with_players.state == State.COLLECTING_ANSWERS
        assert len(room_with_players.answers) == 0  # Should be reset
        assert len(room_with_players.votes) == 0
    
    def test_game_ends_after_all_rounds(self, room_with_players):
        """Test game ends after completing all rounds"""
        room_with_players.start()
        initial_rounds = PromptRoom.ROUNDS
        
        # Complete all rounds
        for round_num in range(initial_rounds):
            # Submit answers
            room_with_players.submit_data("alice", {"answer": f"answer1_{round_num}"})
            room_with_players.submit_data("bob", {"answer": f"answer2_{round_num}"})
            room_with_players.submit_data("charlie", {"answer": f"answer3_{round_num}"})
            
            # Submit votes
            room_with_players.submit_data("alice", {"voted_for_answer_id": "bob"})
            room_with_players.submit_data("bob", {"voted_for_answer_id": "charlie"})
            room_with_players.submit_data("charlie", {"voted_for_answer_id": "alice"})
            
            # Advance from results - need to submit data to trigger __next_round
            with patch('time.sleep'):
                room_with_players.submit_data("alice", {})
        
        assert room_with_players.state == State.DONE
        assert room_with_players.round == initial_rounds
    
    def test_get_room_state_waiting_to_start(self, room_with_players):
        """Test getting room state while waiting to start"""
        code, state, data = room_with_players.get_room_state("alice")
        # The original code returns WRONG_STATE for WAITING_TO_START, which seems like a bug
        # But we'll test the actual behavior for now
        assert code == InteractReturnCodes.SUCCESS
        assert state == State.WAITING_TO_START
    
    def test_get_room_state_collecting_answers(self, room_with_players):
        """Test getting room state during answer collection"""
        room_with_players.start()
        
        code, state, data = room_with_players.get_room_state("alice")
        assert code == InteractReturnCodes.SUCCESS
        assert state == State.COLLECTING_ANSWERS
        assert isinstance(data, str)  # Should be the prompt
    
    def test_get_room_state_voting(self, room_with_players):
        """Test getting room state during voting"""
        room_with_players.start()
        
        # Move to voting phase
        room_with_players.submit_data("alice", {"answer": "answer1"})
        room_with_players.submit_data("bob", {"answer": "answer2"})
        room_with_players.submit_data("charlie", {"answer": "answer3"})
        
        code, state, data = room_with_players.get_room_state("alice")
        assert code == InteractReturnCodes.SUCCESS
        assert state == State.VOTING
        assert isinstance(data, dict)
        assert "prompt" in data
        assert "answers" in data
        assert isinstance(data["answers"], list)
    
    def test_get_room_state_voting_no_player(self, room_with_players):
        """Test getting room state during voting with no player specified"""
        room_with_players.start()
        
        # Move to voting phase
        room_with_players.submit_data("alice", {"answer": "answer1"})
        room_with_players.submit_data("bob", {"answer": "answer2"})
        room_with_players.submit_data("charlie", {"answer": "answer3"})
        
        code, state, data = room_with_players.get_room_state(None)
        assert code == InteractReturnCodes.PLAYER_NOT_FOUND
        assert state == State.VOTING
    
    def test_get_room_state_showing_results(self, room_with_players):
        """Test getting room state during results"""
        room_with_players.start()
        
        # Complete a round to get to results
        room_with_players.submit_data("alice", {"answer": "answer1"})
        room_with_players.submit_data("bob", {"answer": "answer2"})
        room_with_players.submit_data("charlie", {"answer": "answer3"})
        
        room_with_players.submit_data("alice", {"voted_for_answer_id": "bob"})
        room_with_players.submit_data("bob", {"voted_for_answer_id": "charlie"})
        room_with_players.submit_data("charlie", {"voted_for_answer_id": "alice"})
        
        code, state, data = room_with_players.get_room_state("alice")
        assert code == InteractReturnCodes.SUCCESS
        assert state == State.SHOWING_RESULTS
        assert isinstance(data, list)
        assert len(data) == 3  # One result per player
        assert all("user" in result and "score" in result for result in data)
    
    def test_scoring_system(self, room_with_players: PromptRoom):
        """Test that scoring works correctly"""
        room_with_players.start()
        
        # Submit answers
        room_with_players.submit_data("alice", {"answer": "answer1"})
        room_with_players.submit_data("bob", {"answer": "answer2"})
        room_with_players.submit_data("charlie", {"answer": "answer3"})
        
        # Players vote - they need to vote for answer IDs from their vote_orders
        # Get the actual vote order for each player to vote correctly
        alice_options = room_with_players.vote_orders["alice"]
        bob_options = room_with_players.vote_orders["bob"] 
        charlie_options = room_with_players.vote_orders["charlie"]
        
        # Have bob and charlie vote for alice (if alice is in their options)
        alice_votes = 0
        if "alice" in alice_options:
            room_with_players.submit_data("alice", {"voted_for_answer_id": "bob"})
        else:
            room_with_players.submit_data("alice", {"voted_for_answer_id": alice_options[0]})
            
        if "alice" in bob_options:
            room_with_players.submit_data("bob", {"voted_for_answer_id": "alice"})
            alice_votes += 1
        else:
            room_with_players.submit_data("bob", {"voted_for_answer_id": bob_options[0]})
            
        if "alice" in charlie_options:
            room_with_players.submit_data("charlie", {"voted_for_answer_id": "alice"})
            alice_votes += 1
        else:
            room_with_players.submit_data("charlie", {"voted_for_answer_id": charlie_options[0]})
        
        room_with_players.state = State.SHOWING_RESULTS
        room_with_players.get_room_state(player=None)
        
        # Check that alice got the expected number of votes
        assert room_with_players.scores["alice"] == alice_votes


class TestGameGateway:
    """Test GameGateway class"""
    
    @pytest.fixture
    def gateway(self):
        """Create a GameGateway instance for testing"""
        return GameGateway()
    
    def test_gateway_initialization(self, gateway):
        """Test gateway initializes correctly"""
        assert isinstance(gateway.rooms, dict)
        assert len(gateway.rooms) == 0
    
    def test_new_game(self, gateway):
        """Test creating a new game"""
        room_id = gateway.new_game(PromptRoom)
        assert len(room_id) == GameGateway.NUM_ROOM_LETTERS
        assert room_id in gateway.rooms
        assert isinstance(gateway.rooms[room_id], PromptRoom)
    
    def test_join_room_success(self, gateway):
        """Test joining a room successfully"""
        room_id = gateway.new_game(PromptRoom)
        result = gateway.join_room(room_id, "alice")
        assert result == JoinReturnCodes.SUCCESS
        assert "alice" in gateway.rooms[room_id].players
    
    def test_join_room_not_found(self, gateway):
        """Test joining non-existent room"""
        result = gateway.join_room("xxxx", "alice")
        assert result == JoinReturnCodes.ROOM_NOT_FOUND
    
    def test_join_room_name_in_use(self, gateway):
        """Test joining room with name already in use"""
        room_id = gateway.new_game(PromptRoom)
        gateway.join_room(room_id, "alice")
        result = gateway.join_room(room_id, "alice")
        assert result == JoinReturnCodes.NAME_IN_USE
    
    def test_rejoin_room_success(self, gateway):
        """Test rejoining a room successfully"""
        room_id = gateway.new_game(PromptRoom)
        gateway.join_room(room_id, "alice")
        result = gateway.rejoin_room(room_id, "alice")
        assert result == JoinReturnCodes.SUCCESS
    
    def test_rejoin_room_not_found(self, gateway):
        """Test rejoining non-existent room"""
        result = gateway.rejoin_room("xxxx", "alice")
        assert result == JoinReturnCodes.ROOM_NOT_FOUND
    
    def test_rejoin_room_name_not_found(self, gateway):
        """Test rejoining room with non-existent name"""
        room_id = gateway.new_game(PromptRoom)
        result = gateway.rejoin_room(room_id, "alice")
        assert result == JoinReturnCodes.NAME_IN_USE  # Player doesn't exist, so can't rejoin
    
    def test_room_start_success(self, gateway):
        """Test starting a room successfully"""
        room_id = gateway.new_game(PromptRoom)
        gateway.join_room(room_id, "alice")
        gateway.join_room(room_id, "bob")
        gateway.join_room(room_id, "charlie")
        
        result = gateway.room_start(room_id)
        assert result == StartReturnCodes.SUCCESS
    
    def test_room_start_not_found(self, gateway):
        """Test starting non-existent room"""
        result = gateway.room_start("xxxx")
        assert result == StartReturnCodes.ROOM_NOT_FOUND
    
    def test_get_room_state_success(self, gateway):
        """Test getting room state successfully"""
        room_id = gateway.new_game(PromptRoom)
        gateway.join_room(room_id, "alice")
        
        code, state, data = gateway.get_room_state(room_id, "alice")
        # The room is in WAITING_TO_START state, which returns WRONG_STATE
        # This seems like a bug in the original code
        assert code == InteractReturnCodes.SUCCESS
        assert isinstance(state, State)
    
    def test_get_room_state_room_not_found(self, gateway):
        """Test getting state of non-existent room"""
        code, state, data = gateway.get_room_state("xxxx", "alice")
        assert code == InteractReturnCodes.ROOM_NOT_FOUND
        assert state == State.UNKNOWN
    
    def test_get_room_state_player_not_found(self, gateway):
        """Test getting room state for non-existent player"""
        room_id = gateway.new_game(PromptRoom)
        
        code, state, data = gateway.get_room_state(room_id, "alice")
        assert code == InteractReturnCodes.PLAYER_NOT_FOUND
        assert state == State.UNKNOWN
    
    def test_submit_data_success(self, gateway):
        """Test submitting data successfully"""
        room_id = gateway.new_game(PromptRoom)
        gateway.join_room(room_id, "alice")
        gateway.join_room(room_id, "bob")
        gateway.join_room(room_id, "charlie")
        gateway.room_start(room_id)
        
        result = gateway.submit_data(room_id, "alice", {"answer": "test"})
        assert result == InteractReturnCodes.SUCCESS
    
    def test_submit_data_room_not_found(self, gateway):
        """Test submitting data to non-existent room"""
        result = gateway.submit_data("xxxx", "alice", {"answer": "test"})
        assert result == InteractReturnCodes.ROOM_NOT_FOUND
    
    def test_submit_data_player_not_found(self, gateway):
        """Test submitting data for non-existent player"""
        room_id = gateway.new_game(PromptRoom)
        result = gateway.submit_data(room_id, "alice", {"answer": "test"})
        assert result == InteractReturnCodes.PLAYER_NOT_FOUND


if __name__ == "__main__":
    pytest.main([__file__])