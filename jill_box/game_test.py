
import string
import json
import random
from enum import Enum, auto
from collections import defaultdict

from typing import (
    List,
    Dict,
    Tuple
)

from jill_box.game import GameGateway, Room, StartReturnCodes, InteractReturnCodes, PromptRoom


def _load_prompts() -> List[Tuple[str, str]]:
    prompts :List[Tuple[str, str]] = []
    with open('jill_box/data/questions.txt') as fd:
        for line in fd.readlines():
            prompts.append(tuple(line.split('\t')))
    return prompts



def main():
    gateway = GameGateway()

    room = gateway.new_game(PromptRoom)

    name1 = "tester1"
    name2 = "tester2"
    name3 = "tester3"

    print(gateway.join_room(room, name1))
    print(gateway.join_room(room, name2))
    print(gateway.join_room(room, name3))

    print(gateway.room_start(room))

    print(gateway.get_room_state(room))

    print(gateway.submit_data(room, name1, {'answer': 'A'}))
    print(gateway.submit_data(room, name2, {'answer': 'B'}))
    print(gateway.submit_data(room, name3, {'answer': 'C'}))

    print(gateway.get_room_state(room))
    print(gateway.get_room_state(room, name2))

    print(gateway.submit_data(room, name1, {'vote': '1'}))
    print(gateway.submit_data(room, name2, {'vote': '0'}))
    print(gateway.submit_data(room, name3, {'vote': '1'}))

    print(gateway.get_room_state(room))

    print(gateway.submit_data(room, name1, {}))
    print(gateway.submit_data(room, name2, {}))
    print(gateway.submit_data(room, name3, {}))


    print(gateway.get_room_state(room))

    print(gateway.submit_data(room, name1, {'answer': 'A2'}))
    print(gateway.submit_data(room, name2, {'answer': 'B2'}))
    print(gateway.submit_data(room, name3, {'answer': 'C2'}))

    print(gateway.get_room_state(room))
    print(gateway.get_room_state(room, name2))

    print(gateway.submit_data(room, name1, {'vote': '0'}))
    print(gateway.submit_data(room, name2, {'vote': '0'}))
    print(gateway.submit_data(room, name3, {'vote': '1'}))

    print(gateway.get_room_state(room))

if __name__ == "__main__":
    main()
