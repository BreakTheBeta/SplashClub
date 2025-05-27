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

# --- Schema Generation Function ---
def generate_json_schemas(output_dir: str = "schemas_pydantic"):
    """Generates JSON schemas for Incoming and Outgoing messages."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Pydantic v2 uses model_json_schema()
    # For discriminated unions, generating schema for the Union itself is best.
    try:
        incoming_schema = IncomingMessage.model_json_schema()
        with open(os.path.join(output_dir, "incoming_messages.json"), "w") as f:
            json.dump(incoming_schema, f, indent=2)
        print(f"Generated schema: {os.path.join(output_dir, 'incoming_messages.json')}")

        outgoing_schema = OutgoingMessage.model_json_schema()
        with open(os.path.join(output_dir, "outgoing_messages.json"), "w") as f:
            json.dump(outgoing_schema, f, indent=2)
        print(f"Generated schema: {os.path.join(output_dir, 'outgoing_messages.json')}")

    except AttributeError:
        # Fallback for Pydantic v1 (less ideal for discriminated unions in schema)
        print("Warning: Using Pydantic v1 style schema generation (less complete for Unions).")
        for model_name, model_type in {"IncomingMessage": IncomingMessage, "OutgoingMessage": OutgoingMessage}.items():
            # Pydantic v1 doesn't have a direct .model_json_schema() for Unions.
            # This will generate for the first type in the Union, or you'd do it for each member.
            # For Pydantic v1, it's often better to generate schema for each individual message type.
            # schema = model_type.schema() # This would be for a single model
            # For simplicity, we'll skip complex v1 union schema generation here.
            # You would typically generate schemas for each member of the Union.
            print(f"Manual schema generation required for {model_name} members with Pydantic v1.")


if __name__ == "__main__":
    print("Generating JSON schemas for WebSocket contracts...")
    generate_json_schemas()
    print("Schema generation complete.")