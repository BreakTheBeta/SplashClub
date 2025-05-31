#!/usr/bin/env python3


import random
import string
from enum import Enum, auto
from abc import ABC, abstractmethod 
import json
import time 

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

from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    Any,
    Type
)

def _random_id() -> str:
    ascii = string.ascii_lowercase
    return "".join(random.choices(ascii, k=GameGateway.NUM_ROOM_LETTERS))

def _load_prompts() -> List[Tuple[str, str]]:
    prompts: List[Tuple[str, str]] = []
    with open('jill_box/data/questions.txt') as fd:
        for line in fd.readlines():
            prompts.append(tuple(line.strip().split('\t')))
    return prompts

class State(Enum):
    WAITING_TO_START = 'WAITING_TO_START'
    COLLECTING_ANSWERS = 'COLLECTING_ANSWERS'
    VOTING = 'VOTING'
    SHOWING_RESULTS = 'SHOWING_RESULTS'
    DONE = 'DONE'
    UNKNOWN = 'UNKNOWN'  # Fixed typo

class JoinReturnCodes(Enum):
    SUCCESS = auto()
    NAME_IN_USE = auto()
    ROOM_NOT_FOUND = auto()

class GetReturnCodes(Enum):
    SUCCESS = auto()
    ROOM_NOT_FOUND = auto()
    NAME_NOT_FOUND = auto()

class StartReturnCodes(Enum):
    SUCCESS = auto()
    TOO_FEW_PLAYERS = auto()
    ALREADY_STARTED = auto()
    ROOM_NOT_FOUND = auto()

class InteractReturnCodes(Enum):
    SUCCESS = auto()
    INVALID_DATA = auto()
    WRONG_STATE = auto()
    ROOM_NOT_FOUND = auto()
    PLAYER_NOT_FOUND = auto()

# Define specific return types for different game states
GameStateData = Union[str, Dict[str, Any], List[Dict[str, Any]], Dict[str, str]]
GameStateReturn = Tuple[InteractReturnCodes, State, GameStateData]

class Player:
    def __init__(self) -> None:
        pass

class Room(ABC):
    def __init__(self) -> None:
        self.players: Dict[str, Player] = {}
    
    def add_player(self, name: str) -> bool:
        if name in self.players.keys():
            return False
        self.players[name] = Player()
        return True
    
    @abstractmethod
    def start(self) -> StartReturnCodes:
        pass
    
    @abstractmethod
    def get_room_state(self, player: Optional[str]) -> GameStateReturn:
        pass
    
    @abstractmethod
    def submit_data(self, player: str, data: Dict[str, Any]) -> InteractReturnCodes:
        pass

class GameGateway:

    NUM_ROOM_LETTERS = 4

    def __init__(self) -> None:
        self.rooms: Dict[str, Room] = {}

    def room_start(self, room: str) -> StartReturnCodes:
        if room not in self.rooms:
            return StartReturnCodes.ROOM_NOT_FOUND
        return self.rooms[room].start()

    def new_game(self, room_class: Type[Room]) -> str:
        room = _random_id()
        self.rooms[room] = room_class()
        return room

    def join_room(self, room: str, name: str) -> JoinReturnCodes:
        try:
            if room not in self.rooms:
                return JoinReturnCodes.ROOM_NOT_FOUND
            success = self.rooms[room].add_player(name)
            if success:
                return JoinReturnCodes.SUCCESS
            else:
                return JoinReturnCodes.NAME_IN_USE
        except Exception:
            return JoinReturnCodes.ROOM_NOT_FOUND

    def get_room_state(self, room: str, name: Optional[str] = None) -> GameStateReturn:
        if room in self.rooms:
            if name is None or name in self.rooms[room].players:
                return self.rooms[room].get_room_state(name)
            else:
                return (InteractReturnCodes.PLAYER_NOT_FOUND, State.UNKNOWN, {})
        return (InteractReturnCodes.ROOM_NOT_FOUND, State.UNKNOWN, {})

    def submit_data(self, room: str, name: str, data: Dict[str, Any]) -> InteractReturnCodes:
        if room in self.rooms:
            if name in self.rooms[room].players:
                return self.rooms[room].submit_data(name, data)
            else:
                return InteractReturnCodes.PLAYER_NOT_FOUND
        return InteractReturnCodes.ROOM_NOT_FOUND

class PromptRoom(Room):

    ROUNDS = 3 
    CORRECT_KEY = "~!~ø~!~"
    PROMPTS = _load_prompts()
  
    def __init__(self) -> None:
        super().__init__()
        
        self.prompts = random.sample(PromptRoom.PROMPTS, PromptRoom.ROUNDS)
        self.state = State.WAITING_TO_START
        self.round = 0
        self.answers: Dict[str, str] = {}
        self.votes: Dict[str, str] = {}
        self.vote_orders: Dict[str, List[str]] = {}
        self.scores: Dict[str, int] = {}  # Fixed type hint
        self.confirmed: Dict[str, bool] = {}

    def start(self) -> StartReturnCodes:
        if self.state != State.WAITING_TO_START:
            return StartReturnCodes.ALREADY_STARTED
        if len(self.players) < 3:
            return StartReturnCodes.TOO_FEW_PLAYERS
        self.state = State.COLLECTING_ANSWERS
        # Initialize scores for all players
        self.scores = {player: 0 for player in self.players.keys()}
        return StartReturnCodes.SUCCESS

    def get_prompt(self) -> str:
        return self.prompts[self.round][0]

    def get_answers(self, user: str) -> List[Dict[str, str]]:  # Fixed method name typo
        return [{'id': p, 'text': self.answers[p]} for p in self.vote_orders[user]]
    
    def __start_voting(self) -> None:
        self.state = State.VOTING
        self.answers[PromptRoom.CORRECT_KEY] = self.prompts[self.round][1]
        for player in self.players:
            other_players = [k for k in self.answers.keys() if k != player]
            self.vote_orders[player] = random.sample(other_players, len(other_players))

    def __show_results(self) -> None:
        self.state = State.SHOWING_RESULTS

    def __votes_to_score(self) -> Dict[str, int]:
        scores = {u: 0 for u in self.players}
        # Count votes for each player
        for voter, voted_for in self.votes.items():
            if voted_for in self.players:
                scores[voted_for] += 1
                # Add to total scores
                if voted_for in self.scores:
                    self.scores[voted_for] += 1
        return scores

    def __next_round(self) -> None:
        self.round += 1
        if self.round < PromptRoom.ROUNDS:
            self.state = State.COLLECTING_ANSWERS
            self.answers = {}
            self.votes = {}
            self.vote_orders = {}
            self.confirmed = {}
        else:
            self.state = State.DONE

    def submit_data(self, player: str, data: Dict[str, Any]) -> InteractReturnCodes:
        try:
            if self.state == State.COLLECTING_ANSWERS:
                if 'answer' not in data:
                    return InteractReturnCodes.INVALID_DATA
                self.answers[player] = str(data['answer']).upper()
                if len(self.answers) == len(self.players):
                    self.__start_voting()
            elif self.state == State.VOTING:
                if 'voted_for_answer_id' not in data:
                    return InteractReturnCodes.INVALID_DATA
                vote = str(data['voted_for_answer_id'])
                self.votes[player] = vote
                if len(self.votes) == len(self.players):
                    self.__show_results()
            elif self.state == State.SHOWING_RESULTS:
                time.sleep(2)
                self.__next_round()
            else:
                return InteractReturnCodes.WRONG_STATE
            return InteractReturnCodes.SUCCESS
        except (KeyError, ValueError, TypeError):
            return InteractReturnCodes.INVALID_DATA

    def get_room_state(self, player: Optional[str]) -> GameStateReturn:
        if self.round >= PromptRoom.ROUNDS:
            return (InteractReturnCodes.SUCCESS, self.state, {})
        elif self.state == State.COLLECTING_ANSWERS:
            return (InteractReturnCodes.SUCCESS, self.state, self.get_prompt())
        elif self.state == State.VOTING:
            if player is None:
                return (InteractReturnCodes.PLAYER_NOT_FOUND, self.state, {})
            answers_data = {
                'prompt': self.prompts[self.round][0], 
                'answers': self.get_answers(player)
            }
            return (InteractReturnCodes.SUCCESS, self.state, answers_data)
        elif self.state == State.SHOWING_RESULTS:
            print("PRINTING OUT RESULTS")
            round_scores = self.__votes_to_score()
            results = [{"user": user, "score": self.scores[user]} for user in self.scores]
            return (InteractReturnCodes.SUCCESS, self.state, results)
        else:
            return (InteractReturnCodes.WRONG_STATE, self.state, {})