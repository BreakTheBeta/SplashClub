#!/usr/bin/env python3

# NOTE: NEEDS SYNCHRONIZATION FOR MULTITHREADING

import random
import string
from enum import Enum, auto
from abc import ABC, abstractmethod 
import json

from typing import (
    Dict,
    List,
    Optional,
    Tuple
)

def _random_id() -> str:
    ascii = string.ascii_lowercase
    return "".join(random.choices(ascii, k=GameGateway.NUM_ROOM_LETTERS))

def _load_prompts() -> List[Tuple[str, str]]:
    prompts :List[Tuple[str, str]] = []
    with open('jill_box/data/questions.txt') as fd:
        for line in fd.readlines():
            prompts.append(tuple(line.split('\t')))
    return prompts

class State(Enum):
    WAITING_TO_START = 'WAITING_TO_START'
    COLLECTING_ANSWERS = 'COLLECTING_ANSWERS'
    VOTING = 'VOTING'
    SHOWING_RESULTS = 'SHOWING_RESULTS'
    DONE = 'DONE'
    UNKONWN = 'UNKONWN'

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


class Player:
    def __init__(self):
        pass

class Room(ABC):
    def __init__(self):
        self.players: Dict[str, Player] = {}
    def add_player(self, name) -> bool:
        if name in self.players.keys():
            return False
        self.players[name] = Player()
        return True
    @abstractmethod
    def start(self) -> StartReturnCodes:
        pass
    @abstractmethod
    def get_room_state(self, player) -> Tuple[InteractReturnCodes, State, str]:
        pass
    @abstractmethod
    def submit_data(self, player, data) -> InteractReturnCodes:
        pass

class GameGateway:

    NUM_ROOM_LETTERS = 4

    def __init__(self):
        self.rooms: Dict[str, Room] = {}

    def room_start(self, room) -> StartReturnCodes:
        if room not in self.rooms:
            return StartReturnCodes.ROOM_NOT_FOUND
        return self.rooms[room].start()

    def new_game(self, room_class) -> str:
        room = _random_id()
        self.rooms[room] = room_class()
        return room

    def join_room(self, room, name) -> JoinReturnCodes:
        try:
            success = self.rooms[room].add_player(name)
            if success:
                return JoinReturnCodes.SUCCESS
            else:
                return JoinReturnCodes.NAME_IN_USE
        except:
            return JoinReturnCodes.ROOM_NOT_FOUND

    def get_room_state(self, room, name=None) -> Tuple[InteractReturnCodes, State, str]:
        if room in self.rooms:
            if name is None or name in self.rooms[room].players:
                return self.rooms[room].get_room_state(name)
            else:
                return (InteractReturnCodes.PLAYER_NOT_FOUND, State.UNKONWN, '')
        return (InteractReturnCodes.ROOM_NOT_FOUND, State.UNKONWN, '')

    def submit_data(self, room, name, data) -> InteractReturnCodes:
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
  
    def __init__(self):
        super().__init__()
        
        self.prompts = random.sample(PromptRoom.PROMPTS, PromptRoom.ROUNDS)
        self.state = State.WAITING_TO_START
        self.round = 0
        self.answers: Dict[str, str] = {}
        self.votes: Dict[str, str] = {}
        self.vote_orders: Dict[str, List[str]] = {}
        self.scores: Dict[Tuple[str, str], int] = {}
        self.confirmed: Dict[str, bool] = {}

    def start(self) -> StartReturnCodes:
        if self.state != State.WAITING_TO_START:
            return StartReturnCodes.ALREADY_STARTED
        if len(self.players) < 3:
            return StartReturnCodes.TOO_FEW_PLAYERS
        self.state = State.COLLECTING_ANSWERS
        return StartReturnCodes.SUCCESS


    def get_prompt(self) -> str:
        return self.prompts[self.round][0]

    def get_anwers(self, user) -> list[dict[str, str]]:
        return [ {'id': p, 'text': self.answers[p]} for p in self.vote_orders[user] ]
    
    def __start_voting(self):
        self.state = State.VOTING
        self.answers[PromptRoom.CORRECT_KEY] = self.prompts[self.round][1]
        for player in self.players:
            other_players = [ k for k in self.answers.keys() if k != player ]
            self.vote_orders[player] = random.sample(other_players, len(other_players))

    def __show_results(self):
        self.state = State.SHOWING_RESULTS
        for name in self.votes.items():
            if name in self.players:
                self.scores[name] += 1

    def __votes_to_score(self):
        scores = { u:0 for u in self.players }
        self.__show_results()
        for name in self.votes.items():
            if name in self.players:
                self.scores[name] += 1
        return scores

    def __next_round(self):
        self.round += 1
        if self.round < PromptRoom.ROUNDS:
            self.state = State.COLLECTING_ANSWERS
            self.answers = {}
            self.votes = {}
            self.vote_orders = {}
            self.confirmed = {}
        else:
            self.state = State.DONE


    def submit_data(self, player, data) -> InteractReturnCodes:
        try:
            if self.state == State.COLLECTING_ANSWERS:
                self.answers[player] = data['answer'].upper()
                if len(self.answers) == len(self.players):
                    self.__start_voting()
            elif self.state == State.VOTING:
                # vote = int(data['vote'])
                vote = str(data['voted_for_answer_id'])
                self.votes[player] = vote
                if len(self.votes) == len(self.players):
                    self.__show_results()
            elif self.state == State.SHOWING_RESULTS:
                self.confirmed[player] = True
                if len(self.confirmed) == len(self.players):
                    self.__next_round()
            else:
                return InteractReturnCodes.WRONG_STATE
            return InteractReturnCodes.SUCCESS
        except:
            return InteractReturnCodes.INVALID_DATA

    def get_room_state(self, player) -> Tuple[InteractReturnCodes, State, str]:
        if self.round == PromptRoom.ROUNDS:
            return (InteractReturnCodes.SUCCESS, self.state, '')
        elif self.state == State.COLLECTING_ANSWERS:
            return (InteractReturnCodes.SUCCESS, self.state, self.get_prompt())
        elif self.state == State.VOTING:
            answers = json.dumps({'prompt': self.prompts[self.round][0], 'answers': self.get_anwers(player)})
            return (InteractReturnCodes.SUCCESS, self.state, answers)
        elif self.state == State.SHOWING_RESULTS:
            print("PRINTING OUT RESULTS")
            # ret = json.dumps({'answer': self.prompts[self.round][1],'earned': self.__votes_to_score(), 'total': self.scores})
            self.__votes_to_score()
            ret = json.dumps([{"user": i, "score": self.scores[i]} for i in self.scores])
            return (InteractReturnCodes.SUCCESS, self.state, ret)
        return (InteractReturnCodes.WRONG_STATE, self.state, '')
