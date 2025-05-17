import pytest
import json
import random
import string
from unittest.mock import patch, mock_open, MagicMock

from jill_box.game import GameGateway, Room, StartReturnCodes, InteractReturnCodes

# Import TestRoom class directly from the test file since it's defined there
# and not in jill_box.game as the error indicated
from room_test import TestRoom

# Sample data for mocking the questions.txt file
MOCK_QUESTIONS = """Question1\tAnswer1
Question2\tAnswer2
Question3\tAnswer3
Question4\tAnswer4
Question5\tAnswer5"""


@pytest.fixture
def mock_questions():
    """Fixture to mock the _load_prompts function to return predefined prompts."""
    with patch("builtins.open", mock_open(read_data=MOCK_QUESTIONS)):
        yield


@pytest.fixture
def test_room(mock_questions):
    """Fixture that provides a TestRoom instance with mocked prompts."""
    # Set a fixed seed to ensure deterministic random behavior
    random.seed(42)
    room = TestRoom()
    # Reset random seed after creating the room to not affect other tests
    random.seed()
    return room


@pytest.fixture
def game_gateway():
    """Fixture that provides a GameGateway instance."""
    return GameGateway()


@pytest.fixture
def populated_room(game_gateway, test_room):
    """Fixture that provides a TestRoom with 3 players already joined."""
    room_id = game_gateway.new_game(lambda: test_room)
    
    # Add three test players
    game_gateway.join_room(room_id, "tester1")
    game_gateway.join_room(room_id, "tester2")
    game_gateway.join_room(room_id, "tester3")
    
    return room_id, test_room


class TestTestRoom:
    """Tests for the TestRoom class."""
    
    def test_init(self, test_room):
        """Test that the TestRoom is properly initialized."""
        assert test_room.state == TestRoom.State.WAITING_TO_START
        assert test_room.round == 0
        assert len(test_room.prompts) == TestRoom.ROUNDS
        assert isinstance(test_room.answers, dict)
        assert isinstance(test_room.votes, dict)
        assert isinstance(test_room,  TestRoom)
    
    def test_start_success(self, test_room):
        """Test that starting a room with enough players succeeds."""
        # Add enough players
        test_room.players = ["player1", "player2", "player3"]
        
        result = test_room.start()
        
        assert result == StartReturnCodes.SUCCESS
        assert test_room.state == TestRoom.State.COLLECTING_ANSWERS
    
    def test_start_too_few_players(self, test_room):
        """Test that starting a room with too few players fails."""
        # Add insufficient players
        test_room.players = ["player1", "player2"]
        
        result = test_room.start()
        
        assert result == StartReturnCodes.TOO_FEW_PLAYERS
        assert test_room.state == TestRoom.State.WAITING_TO_START
    
    def test_start_already_started(self, test_room):
        """Test that starting an already started room fails."""
        # Set state to something other than WAITING_TO_START
        test_room.state = TestRoom.State.COLLECTING_ANSWERS
        
        result = test_room.start()
        
        assert result == StartReturnCodes.ALREADY_STARTED
    
    def test_get_prompt(self, test_room):
        """Test that get_prompt returns the correct prompt for the current round."""
        prompt = test_room.get_prompt()
        assert prompt == test_room.prompts[0][0]
    
    def test_submit_data_collecting_answers(self, test_room):
        """Test submitting an answer during COLLECTING_ANSWERS state."""
        # Setup
        test_room.players = ["player1", "player2", "player3"]
        test_room.state = TestRoom.State.COLLECTING_ANSWERS
        
        # Submit data for the first player
        result = test_room.submit_data("player1", {"answer": "Test Answer"})
        
        # Verify
        assert result == InteractReturnCodes.SUCCESS
        assert test_room.answers["player1"] == "TEST ANSWER"
        assert test_room.state == TestRoom.State.COLLECTING_ANSWERS  # State should not change yet
        
        # Submit data for the remaining players
        test_room.submit_data("player2", {"answer": "Another Answer"})
        result = test_room.submit_data("player3", {"answer": "Final Answer"})
        
        # Verify state changes after all players submit
        assert result == InteractReturnCodes.SUCCESS
        assert test_room.state == TestRoom.State.VOTING
        assert TestRoom.CORRECT_KEY in test_room.answers
    
    def test_submit_data_voting(self, test_room):
        """Test submitting a vote during VOTING state."""
        # Setup
        test_room.players = ["player1", "player2", "player3"]
        test_room.state = TestRoom.State.VOTING
        test_room.round = 0
        test_room.answers = {"player1": "ANSWER1", "player2": "ANSWER2", "player3": "ANSWER3", TestRoom.CORRECT_KEY: "CORRECT"}
        
        # Create vote orders for players
        test_room.vote_orders = {
            "player1": ["player2", "player3", TestRoom.CORRECT_KEY],
            "player2": ["player1", "player3", TestRoom.CORRECT_KEY],
            "player3": ["player1", "player2", TestRoom.CORRECT_KEY]
        }
        
        # Submit votes for all players
        test_room.submit_data("player1", {"vote": "0"})
        test_room.submit_data("player2", {"vote": "1"})
        result = test_room.submit_data("player3", {"vote": "2"})
        
        # Verify
        assert result == InteractReturnCodes.SUCCESS
        assert test_room.state == TestRoom.State.SHOWING_RESULTS
        assert len(test_room.votes) == 3
        assert test_room.votes["player1"] == "player2"
        assert test_room.votes["player2"] == "player3"
        assert test_room.votes["player3"] == TestRoom.CORRECT_KEY
    
    def test_submit_data_showing_results(self, test_room):
        """Test confirming results during SHOWING_RESULTS state."""
        # Setup
        test_room.players = ["player1", "player2", "player3"]
        test_room.state = TestRoom.State.SHOWING_RESULTS
        test_room.round = 0
        
        # Submit confirmations for all players
        test_room.submit_data("player1", {})
        test_room.submit_data("player2", {})
        result = test_room.submit_data("player3", {})
        
        # Verify
        assert result == InteractReturnCodes.SUCCESS
        assert test_room.state == TestRoom.State.COLLECTING_ANSWERS
        assert test_room.round == 1
        assert len(test_room.answers) == 0
        assert len(test_room.votes) == 0
    
    def test_next_round_to_done(self, test_room):
        """Test that the game transitions to DONE after all rounds."""
        # Setup
        test_room.players = ["player1", "player2", "player3"]
        test_room.state = TestRoom.State.SHOWING_RESULTS
        test_room.round = TestRoom.ROUNDS - 1  # Last round
        
        # Confirm all players
        test_room.submit_data("player1", {})
        test_room.submit_data("player2", {})
        test_room.submit_data("player3", {})
        
        # Verify
        assert test_room.state == TestRoom.State.DONE
        assert test_room.round == TestRoom.ROUNDS
    
    def test_submit_data_invalid(self, test_room):
        """Test submitting invalid data."""
        # Setup
        test_room.players = ["player1", "player2", "player3"]
        test_room.state = TestRoom.State.COLLECTING_ANSWERS
        
        # Submit invalid data
        result = test_room.submit_data("player1", {"wrong_key": "Some value"})
        
        # Verify
        assert result == InteractReturnCodes.INVALID_DATA
    
    def test_submit_data_wrong_state(self, test_room):
        """Test submitting data in the wrong state."""
        # Setup
        test_room.players = ["player1", "player2", "player3"]
        test_room.state = TestRoom.State.DONE
        
        # Submit data in wrong state
        result = test_room.submit_data("player1", {"answer": "Test"})
        
        # Verify
        assert result == InteractReturnCodes.WRONG_STATE
    
    def test_get_answers(self, test_room):
        """Test getting answers for voting."""
        # Setup
        test_room.answers = {
            "player1": "ANSWER1", 
            "player2": "ANSWER2", 
            "player3": "ANSWER3",
            TestRoom.CORRECT_KEY: "CORRECT"
        }
        test_room.vote_orders = {
            "player1": ["player2", "player3", TestRoom.CORRECT_KEY]
        }
        
        # Get answers for specific player
        answers = test_room.get_anwers("player1")
        
        # Verify
        assert answers == ["ANSWER2", "ANSWER3", "CORRECT"]
        
        # Get random answers
        random_answers = test_room.get_anwers(None)
        
        # Verify
        assert len(random_answers) == 4
        for answer in ["ANSWER1", "ANSWER2", "ANSWER3", "CORRECT"]:
            assert answer in random_answers
    
    def test_get_room_state_collecting_answers(self, test_room):
        """Test getting room state during COLLECTING_ANSWERS state."""
        # Setup
        test_room.state = TestRoom.State.COLLECTING_ANSWERS
        test_room.round = 0
        
        # Get room state
        code, state, data = test_room.get_room_state("player1")
        
        # Verify
        assert code == InteractReturnCodes.SUCCESS
        assert state == TestRoom.State.COLLECTING_ANSWERS
        assert data == test_room.get_prompt()
    
    def test_get_room_state_voting(self, test_room):
        """Test getting room state during VOTING state."""
        # Setup
        test_room.state = TestRoom.State.VOTING
        test_room.round = 0
        test_room.prompts = [("Question", "Answer")]
        test_room.answers = {"player1": "ANSWER1", "player2": "ANSWER2"}
        test_room.vote_orders = {"player1": ["player2"]}
        
        # Get room state
        code, state, data = test_room.get_room_state("player1")
        
        # Verify
        assert code == InteractReturnCodes.SUCCESS
        assert state == TestRoom.State.VOTING
        
        data_dict = json.loads(data)
        assert data_dict["prompt"] == "Question"
        assert data_dict["answers"] == ["ANSWER2"]
    
    def test_get_room_state_showing_results(self, test_room):
        """Test getting room state during SHOWING_RESULTS state."""
        # Setup
        test_room.state = TestRoom.State.SHOWING_RESULTS
        test_room.round = 0
        test_room.prompts = [("Question", "Answer")]
        test_room.players = ["player1", "player2"]
        test_room.votes = {"player1": "player2", "player2": "player1"}
        test_room.scores = {"player1": 1, "player2": 1}
        
        # Get room state
        code, state, data = test_room.get_room_state("player1")
        
        # Verify
        assert code == InteractReturnCodes.SUCCESS
        assert state == TestRoom.State.SHOWING_RESULTS
        
        data_dict = json.loads(data)
        assert data_dict["answer"] == "Answer"
        assert "earned" in data_dict
        assert "total" in data_dict
    
    def test_get_room_state_done(self, test_room):
        """Test getting room state when game is done."""
        # Setup
        test_room.state = TestRoom.State.DONE
        test_room.round = TestRoom.ROUNDS
        
        # Get room state
        code, state, data = test_room.get_room_state("player1")
        
        # Verify
        assert code == InteractReturnCodes.SUCCESS
        assert state == TestRoom.State.DONE
        assert data == ''
    
    def test_get_room_state_wrong_state(self, test_room):
        """Test getting room state with an invalid state."""
        # Setup a state that doesn't match any expected state
        test_room.state = "INVALID_STATE"
        test_room.round = 0
        
        # Get room state
        code, state, data = test_room.get_room_state("player1")
        
        # Verify
        assert code == InteractReturnCodes.WRONG_STATE


class TestGameGateway:
    """Tests for the GameGateway's interaction with TestRoom."""
    
    def test_join_room(self, populated_room):
        """Test joining a room via the gateway."""
        room_id, test_room = populated_room
        
        # Verify players were added
        assert len(test_room.players) == 3
        assert "tester1" in test_room.players
        assert "tester2" in test_room.players
        assert "tester3" in test_room.players
    
    def test_room_start(self, game_gateway, populated_room):
        """Test starting a room via the gateway."""
        room_id, test_room = populated_room
        
        # Start the room
        result = game_gateway.room_start(room_id)
        
        # Verify
        assert result == StartReturnCodes.SUCCESS
        assert test_room.state == TestRoom.State.COLLECTING_ANSWERS
    
    def test_game_flow(self, game_gateway, populated_room):
        """Test the full game flow through gateway."""
        room_id, test_room = populated_room
        
        # Start the game
        game_gateway.room_start(room_id)
        assert test_room.state == TestRoom.State.COLLECTING_ANSWERS
        
        # Get room state
        code, state, data = game_gateway.get_room_state(room_id)
        assert code == InteractReturnCodes.SUCCESS
        assert state == TestRoom.State.COLLECTING_ANSWERS
        
        # Submit answers
        game_gateway.submit_data(room_id, "tester1", {"answer": "A"})
        game_gateway.submit_data(room_id, "tester2", {"answer": "B"})
        game_gateway.submit_data(room_id, "tester3", {"answer": "C"})
        
        # Verify state changed to voting
        assert test_room.state == TestRoom.State.VOTING
        
        # Get room state for voting
        code, state, data = game_gateway.get_room_state(room_id, "tester2")
        assert state == TestRoom.State.VOTING
        
        # Submit votes
        game_gateway.submit_data(room_id, "tester1", {"vote": "1"})
        game_gateway.submit_data(room_id, "tester2", {"vote": "0"})
        game_gateway.submit_data(room_id, "tester3", {"vote": "1"})
        
        # Verify state changed to showing results
        assert test_room.state == TestRoom.State.SHOWING_RESULTS
        
        # Submit confirmations
        game_gateway.submit_data(room_id, "tester1", {})
        game_gateway.submit_data(room_id, "tester2", {})
        game_gateway.submit_data(room_id, "tester3", {})
        
        # Verify state changed back to collecting answers for next round
        assert test_room.state == TestRoom.State.COLLECTING_ANSWERS
        assert test_room.round == 1


if __name__ == "__main__":
    pytest.main(["-v"])
