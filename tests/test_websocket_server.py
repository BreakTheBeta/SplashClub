import asyncio
import json
from typing import Self
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from collections import defaultdict

# Mock websockets module
class MockConnectionClosed(Exception):
    def __init__(self, code=None, reason=None):
        self.code = code
        self.reason = reason

class MockConnectionClosedOK(MockConnectionClosed):
    pass

class MockConnectionClosedError(MockConnectionClosed):
    pass

# Mock websockets exceptions
class MockWebsocketsExceptions:
    ConnectionClosed = MockConnectionClosed
    ConnectionClosedOK = MockConnectionClosedOK
    ConnectionClosedError = MockConnectionClosedError

# Mock websockets module
class MockWebsockets:
    exceptions = MockWebsocketsExceptions

# Functions to test (simplified implementations for testing)
USERS = defaultdict(dict) # type: ignore
WEBSOCKET_TO_USER_INFO = {}

async def safe_websocket_send(websocket, message_json: str):
    """Safely sends a JSON message, raising ConnectionClosed on failure."""
    try:
        await websocket.send(message_json)
    except Exception as e:
        if "ConnectionClosed" in str(type(e)):
            raise MockConnectionClosed() from e
        raise

async def broadcast_to_room(room_id: str, message_dict: dict):
    """Broadcasts a message to all users in a specific room."""
    if room_id not in USERS:
        return

    message_json = json.dumps(message_dict)
    current_connections = list(USERS.get(room_id, {}).items())
    
    if not current_connections:
        return

    tasks = [
        safe_websocket_send(ws, message_json)
        for _, ws in current_connections
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            user_id, ws = current_connections[i]
            print(f"Broadcast failed for user {user_id}")

async def notify_users_of_room_update(room_id: str):
    """Sends UserUpdateServerMessage to all users in the room."""
    if room_id in USERS and USERS[room_id]:
        current_users_in_room = list(USERS[room_id].keys())
        update_msg = {"type": "user_update", "users": current_users_in_room}
        await broadcast_to_room(room_id, update_msg)

async def unregister_user(websocket):
    """Removes a user from global tracking and notifies others in their room."""
    user_info = WEBSOCKET_TO_USER_INFO.pop(websocket, None)
    if user_info:
        room_id = user_info["room_id"]
        user_id = user_info["user_id"]
        
        if room_id in USERS and user_id in USERS[room_id]:
            del USERS[room_id][user_id]
            if not USERS[room_id]:  # Room is empty
                del USERS[room_id]
            else:
                # Notify remaining users about the disconnection
                await notify_users_of_room_update(room_id)

def register_user(websocket, room_id: str, user_id: str):
    """Register a user in a room."""
    USERS[room_id][user_id] = websocket
    WEBSOCKET_TO_USER_INFO[websocket] = {"room_id": room_id, "user_id": user_id}

# Test fixtures
@pytest.fixture
def mock_websocket():
    """Create a mock websocket connection."""
    ws = AsyncMock()
    ws.remote_address = ('127.0.0.1', 12345)
    return ws

@pytest.fixture
def another_mock_websocket():
    """Create another mock websocket connection."""
    ws = AsyncMock()
    ws.remote_address = ('127.0.0.1', 12346)
    return ws

@pytest.fixture(autouse=True)
def reset_globals():
    """Reset global state before each test."""
    global USERS, WEBSOCKET_TO_USER_INFO
    USERS.clear()
    WEBSOCKET_TO_USER_INFO.clear()


class TestWebSocketFunctions:
    """Test suite for WebSocket server functions."""
    
    @pytest.mark.asyncio
    async def test_safe_websocket_send_success(self, mock_websocket):
        """Test successful websocket message sending."""
        message = '{"type": "test", "data": "hello"}'
        await safe_websocket_send(mock_websocket, message)
        mock_websocket.send.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_safe_websocket_send_connection_closed(self, mock_websocket):
        """Test websocket send when connection is closed."""
        mock_websocket.send.side_effect = MockConnectionClosed()
        
        with pytest.raises(MockConnectionClosed):
            await safe_websocket_send(mock_websocket, "test message")

    @pytest.mark.asyncio
    async def test_broadcast_to_room_single_user(self, mock_websocket):
        """Test broadcasting to room with single user."""
        room_id = "room123"
        user_id = "user1"
        
        # Register user
        register_user(mock_websocket, room_id, user_id)
        
        message = {"type": "test", "content": "hello"}
        await broadcast_to_room(room_id, message)
        
        # Verify message was sent
        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        sent_message = json.loads(call_args)
        assert sent_message["type"] == "test"
        assert sent_message["content"] == "hello"

    @pytest.mark.asyncio
    async def test_broadcast_to_room_multiple_users(self, mock_websocket, another_mock_websocket):
        """Test broadcasting to room with multiple users."""
        room_id = "room123"
        
        # Register multiple users
        register_user(mock_websocket, room_id, "user1")
        register_user(another_mock_websocket, room_id, "user2")
        
        message = {"type": "announcement", "text": "Game starting!"}
        await broadcast_to_room(room_id, message)
        
        # Verify both users received the message
        mock_websocket.send.assert_called_once()
        another_mock_websocket.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_room(self):
        """Test broadcasting to non-existent room."""
        room_id = "nonexistent"
        message = {"type": "test"}
        
        # Should not raise error
        await broadcast_to_room(room_id, message)

    @pytest.mark.asyncio
    async def test_broadcast_with_failed_connection(self, mock_websocket, another_mock_websocket):
        """Test broadcasting when one connection fails."""
        room_id = "room123"
        
        # Register users
        register_user(mock_websocket, room_id, "user1")
        register_user(another_mock_websocket, room_id, "user2")
        
        # Make one connection fail
        mock_websocket.send.side_effect = MockConnectionClosed()
        
        message = {"type": "test"}
        await broadcast_to_room(room_id, message)
        
        # Verify the working connection still received the message
        another_mock_websocket.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_users_of_room_update(self, mock_websocket, another_mock_websocket):
        """Test notifying users of room updates."""
        room_id = "room123"
        
        # Register users
        register_user(mock_websocket, room_id, "user1")
        register_user(another_mock_websocket, room_id, "user2")
        
        await notify_users_of_room_update(room_id)
        
        # Verify UserUpdate message was sent to both users
        assert mock_websocket.send.called
        assert another_mock_websocket.send.called
        
        # Check message content
        call_args = mock_websocket.send.call_args[0][0]
        sent_message = json.loads(call_args)
        assert sent_message["type"] == "user_update"
        assert set(sent_message["users"]) == {"user1", "user2"}

    @pytest.mark.asyncio
    async def test_register_user(self, mock_websocket):
        """Test user registration."""
        room_id = "room123"
        user_id = "testuser"
        
        register_user(mock_websocket, room_id, user_id)
        
        # Verify user was registered
        assert USERS[room_id][user_id] == mock_websocket
        assert WEBSOCKET_TO_USER_INFO[mock_websocket] == {
            "room_id": room_id,
            "user_id": user_id
        }

    @pytest.mark.asyncio
    async def test_unregister_user_with_others_in_room(self, mock_websocket, another_mock_websocket):
        """Test user unregistration when others remain in room."""
        room_id = "room123"
        
        # Register two users
        register_user(mock_websocket, room_id, "user1")
        register_user(another_mock_websocket, room_id, "user2")
        
        # Unregister first user
        await unregister_user(mock_websocket)
        
        # Verify user was removed but room still exists
        assert "user1" not in USERS[room_id]
        assert "user2" in USERS[room_id]
        assert mock_websocket not in WEBSOCKET_TO_USER_INFO
        
        # Verify remaining user was notified
        another_mock_websocket.send.assert_called()

    @pytest.mark.asyncio
    async def test_unregister_last_user_removes_room(self, mock_websocket):
        """Test that room is removed when last user leaves."""
        room_id = "room123"
        user_id = "user1"
        
        # Register single user
        register_user(mock_websocket, room_id, user_id)
        
        # Unregister user
        await unregister_user(mock_websocket)
        
        # Verify user and room were removed
        assert room_id not in USERS
        assert mock_websocket not in WEBSOCKET_TO_USER_INFO

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_user(self, mock_websocket):
        """Test unregistering a user that wasn't registered."""
        # Should not raise error
        await unregister_user(mock_websocket)
        
        # Verify no state was modified
        assert len(USERS) == 0
        assert len(WEBSOCKET_TO_USER_INFO) == 0

    def test_multiple_users_same_room(self, mock_websocket, another_mock_websocket):
        """Test registering multiple users in the same room."""
        room_id = "room123"
        
        register_user(mock_websocket, room_id, "user1")
        register_user(another_mock_websocket, room_id, "user2")
        
        # Verify both users are in the same room
        assert len(USERS[room_id]) == 2
        assert "user1" in USERS[room_id]
        assert "user2" in USERS[room_id]

    def test_users_different_rooms(self, mock_websocket, another_mock_websocket):
        """Test users in different rooms."""
        register_user(mock_websocket, "room1", "user1")
        register_user(another_mock_websocket, "room2", "user2")
        
        # Verify users are in separate rooms
        assert len(USERS) == 2
        assert "user1" in USERS["room1"]
        assert "user2" in USERS["room2"]

    @pytest.mark.asyncio
    async def test_broadcast_to_specific_room_only(self, mock_websocket, another_mock_websocket):
        """Test that broadcast only affects the specified room."""
        # Register users in different rooms
        register_user(mock_websocket, "room1", "user1")
        register_user(another_mock_websocket, "room2", "user2")
        
        message = {"type": "room1_message"}
        await broadcast_to_room("room1", message)
        
        # Verify only room1 user received the message
        mock_websocket.send.assert_called_once()
        another_mock_websocket.send.assert_not_called()


# Additional integration-style tests
class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""
    
    @pytest.mark.asyncio
    async def test_user_join_leave_flow(self, mock_websocket):
        """Test complete user join and leave flow."""
        room_id = "room123"
        user_id = "testuser"
        
        # User joins
        register_user(mock_websocket, room_id, user_id)
        assert USERS[room_id][user_id] == mock_websocket
        
        # Send a message to the room
        message = {"type": "welcome", "text": "Hello!"}
        await broadcast_to_room(room_id, message)
        mock_websocket.send.assert_called_once()
        
        # User leaves
        await unregister_user(mock_websocket)
        assert room_id not in USERS
        assert mock_websocket not in WEBSOCKET_TO_USER_INFO

    @pytest.mark.asyncio
    async def test_multiple_users_join_one_leaves(self, mock_websocket, another_mock_websocket):
        """Test scenario where multiple users join and one leaves."""
        room_id = "room123"
        
        # Both users join
        register_user(mock_websocket, room_id, "user1")
        register_user(another_mock_websocket, room_id, "user2")
        
        # Verify both are in room
        assert len(USERS[room_id]) == 2
        
        # One user leaves
        await unregister_user(mock_websocket)
        
        # Verify room still exists with remaining user
        assert len(USERS[room_id]) == 1
        assert "user2" in USERS[room_id]
        
        # Verify remaining user was notified
        another_mock_websocket.send.assert_called()

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent user registration and broadcasting."""
        room_id = "room123"
        websockets = [AsyncMock() for _ in range(5)]
        
        # Register multiple users concurrently
        tasks = []
        for i, ws in enumerate(websockets):
            ws.remote_address = ('127.0.0.1', 12345 + i)
            register_user(ws, room_id, f"user{i}")
        
        # Verify all users registered
        assert len(USERS[room_id]) == 5
        
        # Broadcast to all users
        message = {"type": "mass_message", "text": "Hello everyone!"}
        await broadcast_to_room(room_id, message)
        
        # Verify all users received the message
        for ws in websockets:
            ws.send.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])