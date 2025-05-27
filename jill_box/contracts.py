# contracts.py
import json
import os
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, TypeAdapter

# --- Client to Server Messages ---

class BaseClientMessage(BaseModel):
    """Base model for messages sent from Client to Server."""
    # 'type' will be part of each specific model for discriminated union
    request_id: Optional[str] = None # Optional unique ID for client requests

class CreateRoomClientMessage(BaseClientMessage):
    type: Literal["create_room"] = "create_room"
    user: str = Field(..., description="User ID of the player creating and joining the room.")

class JoinRoomClientMessage(BaseClientMessage):
    type: Literal["join_room"] = "join_room"
    room: str = Field(..., description="ID of the room to join.")
    user: str = Field(..., description="User ID of the player joining.")

class StartRoomClientMessage(BaseClientMessage):
    type: Literal["start_room"] = "start_room"
    room: str = Field(..., description="ID of the room to start.")
    # user: Optional[str] = None # User initiating start, could be inferred by server

class SubmitAnswerClientMessage(BaseClientMessage):
    type: Literal["submit_answer"] = "submit_answer"
    room: str = Field(..., description="ID of the room.")
    user: str = Field(..., description="User ID of the player submitting the answer.")
    answer: str = Field(..., description="The text of the answer being submitted.")

class SubmitVoteClientMessage(BaseClientMessage):
    type: Literal["submit_vote"] = "submit_vote"
    room: str = Field(..., description="ID of the room.")
    user: str = Field(..., description="User ID of the player submitting the vote.")
    voted_for_answer_id: str = Field(..., description="The ID of the answer being voted for.")

# Union of all possible messages from Client to Server
# Pydantic will use the 'type' field to discriminate the union
IncomingMessage = Union[
    CreateRoomClientMessage,
    JoinRoomClientMessage,
    StartRoomClientMessage,
    SubmitAnswerClientMessage,
    SubmitVoteClientMessage,
]

# --- Server to Client Messages ---

class BaseServerMessage(BaseModel):
    """Base model for messages sent from Server to Client."""
    response_to_request_id: Optional[str] = None # Correlates to client's request_id

class ErrorServerMessage(BaseServerMessage):
    type: Literal["error"] = "error"
    message: str = Field(..., description="Error message detailing what went wrong.")
    # code: Optional[str] = None # Could hold the original error enum name or a numeric code

class JoinRoomSuccessServerMessage(BaseServerMessage):
    type: Literal["join_room_ok"] = "join_room_ok" # Differentiated from client's join_room
    room: str = Field(..., description="ID of the room joined.")
    user: str = Field(..., description="User ID of the player who joined.")
    # initial_users_in_room: Optional[List[str]] = None # Could be sent immediately

class UserUpdateServerMessage(BaseServerMessage):
    type: Literal["user_update"] = "user_update"
    # room: str # Client usually knows its room context
    users: List[str] = Field(..., description="Current list of user IDs in the room.")

class AskPromptServerMessage(BaseServerMessage):
    type: Literal["ask_prompt"] = "ask_prompt"
    prompt: str = Field(..., description="The prompt/question for the current round.")

class AnswerOptionForVote(BaseModel):
    id: str = Field(..., description="Unique ID for this answer option.")
    text: str = Field(..., description="The text content of the answer option.")

class AskVoteServerMessage(BaseServerMessage):
    type: Literal["ask_vote"] = "ask_vote"
    prompt: str = Field(..., description="Original prompt")
    answers: List[AnswerOptionForVote] = Field(..., description="List of answers to vote on.")

class ResultDetail(BaseModel):
    user: str = Field(..., description="ID of the answer.")
    score: int = Field(..., description="Score user has totaled over the game")
    # submitter_user_id: Optional[str] = None # Could be included

class ShowResultsServerMessage(BaseServerMessage):
    type: Literal["show_results"] = "show_results"
    results: List[ResultDetail] = Field(..., description="The results of the voting round.")

class GameDoneServerMessage(BaseServerMessage):
    type: Literal["game_done"] = "game_done"
    # room: Optional[str] = None # Context if needed
    message: str = Field(default="The game has ended. Thanks for playing!", description="A message indicating the game is over.")


# Union of all possible messages from Server to Client
OutgoingMessage = Union[
    ErrorServerMessage,
    JoinRoomSuccessServerMessage,
    UserUpdateServerMessage,
    AskPromptServerMessage,
    AskVoteServerMessage,
    ShowResultsServerMessage,
    GameDoneServerMessage,
]

# --- HELPERS ----

def parse_incoming_message(json_str: str) -> IncomingMessage:
    """Parse incoming JSON message into appropriate Pydantic model."""
    adapter = TypeAdapter(IncomingMessage)
    return adapter.validate_json(json_str)

def parse_outgoing_message(json_str: str) -> OutgoingMessage:
    """Parse outgoing JSON message into appropriate Pydantic model."""
    adapter = TypeAdapter(OutgoingMessage)
    return adapter.validate_json(json_str)


# --- Schema Generation Function ---
def generate_json_schemas(output_dir: str = "schemas_pydantic"):
    """Generates JSON schemas for Incoming and Outgoing messages."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # Use TypeAdapter for Union schema generation
        incoming_adapter = TypeAdapter(IncomingMessage)
        incoming_schema = incoming_adapter.json_schema()
        
        with open(os.path.join(output_dir, "incoming_messages.json"), "w") as f:
            json.dump(incoming_schema, f, indent=2)
        print(f"Generated schema: {os.path.join(output_dir, 'incoming_messages.json')}")

        outgoing_adapter = TypeAdapter(OutgoingMessage)
        outgoing_schema = outgoing_adapter.json_schema()
        
        with open(os.path.join(output_dir, "outgoing_messages.json"), "w") as f:
            json.dump(outgoing_schema, f, indent=2)
        print(f"Generated schema: {os.path.join(output_dir, 'outgoing_messages.json')}")

    except Exception as e:
        print(f"Error generating schemas: {e}")
        
        # Fallback: Generate schemas for individual message types
        print("Falling back to individual message type schemas...")
        
        # Client message schemas
        client_messages = [
            ("CreateRoomClientMessage", CreateRoomClientMessage),
            ("JoinRoomClientMessage", JoinRoomClientMessage),
            ("StartRoomClientMessage", StartRoomClientMessage),
            ("SubmitAnswerClientMessage", SubmitAnswerClientMessage),
            ("SubmitVoteClientMessage", SubmitVoteClientMessage),
        ]
        
        # Server message schemas
        server_messages = [
            ("ErrorServerMessage", ErrorServerMessage),
            ("JoinRoomSuccessServerMessage", JoinRoomSuccessServerMessage),
            ("UserUpdateServerMessage", UserUpdateServerMessage),
            ("AskPromptServerMessage", AskPromptServerMessage),
            ("AskVoteServerMessage", AskVoteServerMessage),
            ("ShowResultsServerMessage", ShowResultsServerMessage),
            ("GameDoneServerMessage", GameDoneServerMessage),
        ]
        
        # Generate individual schemas
        for name, model_class in client_messages + server_messages:
            try:
                schema = model_class.model_json_schema()
                with open(os.path.join(output_dir, f"{name}.json"), "w") as f:
                    json.dump(schema, f, indent=2)
                print(f"Generated schema: {os.path.join(output_dir, f'{name}.json')}")
            except Exception as model_error:
                print(f"Failed to generate schema for {name}: {model_error}")

# --- Usage Examples ---
def example_usage():
    """Examples of how to use the message contracts."""
    
    # Example: Creating a client message
    create_room_msg = CreateRoomClientMessage(
        user="player1",
        request_id="req_123"
    )
    json_str = create_room_msg.model_dump_json()
    print(f"Serialized message: {json_str}")
    
    # Example: Parsing incoming JSON
    try:
        parsed = parse_incoming_message(json_str)
        print(f"Parsed message type: {parsed.type}")
        print(f"Message content: {parsed}")
    except Exception as e:
        print(f"Failed to parse message: {e}")
    
    # Example: Creating a server response
    success_response = JoinRoomSuccessServerMessage(
        room="room_456",
        user="player1",
        response_to_request_id="req_123"
    )
    print(f"Server response: {success_response.model_dump_json()}")

if __name__ == "__main__":
    print("Generating JSON schemas for WebSocket contracts...")
    generate_json_schemas()
    print("Schema generation complete.")
    
    print("\nRunning usage examples...")
    example_usage()