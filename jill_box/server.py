#!/usr/bin/env python

# WS server example that synchronizes state across clients

import asyncio
import json
import logging
from enum import Enum
from collections import defaultdict
from typing import Dict
import websockets
from jill_box.game import GameGateway, Room, StartReturnCodes, InteractReturnCodes, JoinReturnCodes
from jill_box.game_test import TestRoom
logging.basicConfig()

USERS: Dict[str, Dict[str, websockets.WebSocketServerProtocol]] = defaultdict(dict)

GATEWAY = GameGateway()

class ClientServerMsgs(Enum):
    create_room = 'create_room'
    join_room = 'join_room'
    start_room = 'start_room'
    submit_answer = 'submit_answer'
    submit_vote = 'submit_vote'


class ServerClientMsgs(Enum):
    error = 'error'
    join_room = 'join_room'
    user_update = 'user_update'
    ask_prompt = 'ask_prompt'
    ask_vote = 'ask_vote'
    show_results = 'show_results'
    game_done = 'game_done'


async def send_error(websocket, error):
    await websocket.send(json.dumps({"type": ServerClientMsgs.error.value, "msg": error.name}))

async def notify_new_users(room):
    if len(USERS.get(room, {})) > 1:  # notify about new users
        print("notifying users")
        messages = {}
        for user in USERS[room].keys():
            others = [other for other in USERS[room].keys()]
            messages[user] = json.dumps({"type": ServerClientMsgs.user_update.value, "users": others})
        
        print(messages)
        
        tasks = []
        for k, websocket in list(USERS[room].items()):
            # We'll try to send and handle exceptions separately
            tasks.append(asyncio.create_task(
                safe_send(websocket, messages[k], room, k)
            ))
        
        if tasks:  # Only wait if there are tasks
            await asyncio.wait(tasks)

# Add this helper function to safely send messages and handle disconnections
async def safe_send(websocket, message, room, user):
    try:
        await websocket.send(message)
    except websockets.exceptions.ConnectionClosed:
        # Connection is closed, remove the user
        if room in USERS and user in USERS[room]:
            USERS[room].pop(user)
            print(f"Removed disconnected user {user} from room {room}")
            # If room is now empty, clean it up
            if not USERS[room]:
                USERS.pop(room)
                print(f"Removed empty room {room}")

async def unregister_user(websocket):
    # Find and remove the user from USERS
    for room in list(USERS.keys()):
        for user, socket in list(USERS[room].items()):
            if socket == websocket:
                USERS[room].pop(user)
                print(f"User {user} disconnected from room {room}")
                # If the room is now empty, you might want to clean it up
                if not USERS[room]:
                    USERS.pop(room)
                else:
                    # Notify other users about the disconnection
                    print("notifying of disconnection")
                    await notify_new_users(room)
                return

async def send_answers(room):
    messages = {}
    for user in USERS[room].keys():
        _, _, answers = GATEWAY.get_room_state(room, user)
        answers = json.loads(answers)
        messages[user] = json.dumps({"type": ServerClientMsgs.ask_vote.value, "answers": answers })
    print(messages)
    # Create tasks from coroutines before passing to asyncio.wait
    tasks = [asyncio.create_task(USERS[room][k].send(messages[k])) for k in messages.keys()]
    await asyncio.wait(tasks)

async def send_results(room):
    ret, _, results = GATEWAY.get_room_state(room)
    results = json.loads(results)
    message = json.dumps({"type": ServerClientMsgs.show_results.value, "results": results})
    print(ret)
    print(message)
    # Create tasks from coroutines before passing to asyncio.wait
    tasks = [asyncio.create_task(websocket.send(message)) for websocket in USERS[room].values()]
    await asyncio.wait(tasks)

async def send_prompt(room):
    ret, _, prompt = GATEWAY.get_room_state(room)
    message = json.dumps({"type": ServerClientMsgs.ask_prompt.value, "prompt": prompt})
    print(ret)
    print(message)
    # Create tasks from coroutines before passing to asyncio.wait
    tasks = [asyncio.create_task(websocket.send(message)) for websocket in USERS[room].values()]
    await asyncio.wait(tasks)

async def start_next_round(room):
    for user in USERS[room].keys():
        GATEWAY.submit_data(room, user, {})
    ret, state, _ = GATEWAY.get_room_state(room)
    print(ret)
    print(state)
    if TestRoom.State(state) == TestRoom.State.COLLECTING_ANSWERS:
        await asyncio.sleep(20)
        await send_prompt(room)
    else:
        message = json.dumps({"type": ServerClientMsgs.game_done.value})
        # Create tasks from coroutines before passing to asyncio.wait
        tasks = [asyncio.create_task(websocket.send(message)) for websocket in USERS[room].values()]
        await asyncio.wait(tasks)

async def counter(websocket):
    async for message in websocket:
        try:
            data = json.loads(message)
            print(data,1)
            
            if ClientServerMsgs(data['type']) == ClientServerMsgs.create_room:
                room = GATEWAY.new_game(TestRoom)
                data['type'] = ClientServerMsgs.join_room.value
                data['room'] = room

            if ClientServerMsgs(data['type']) == ClientServerMsgs.join_room:
                ret = GATEWAY.join_room(data['room'], data['user'])
                if ret == JoinReturnCodes.SUCCESS:
                    await websocket.send(json.dumps(data))
                    USERS[data['room']][data['user']] = websocket
                    print("join room message being sent")
                    await notify_new_users(data['room'])
                else:
                    await send_error(websocket ,ret)           

            if ClientServerMsgs(data['type']) == ClientServerMsgs.start_room:
                ret = GATEWAY.room_start(data['room'])
                if ret == StartReturnCodes.SUCCESS:
                    await send_prompt(data['room'])
                else:
                    await send_error(websocket, ret)    
            if ClientServerMsgs(data['type']) == ClientServerMsgs.submit_answer:
                ret = GATEWAY.submit_data(data['room'], data['user'], data)
                if ret == InteractReturnCodes.SUCCESS:
                    ret, state, _ = GATEWAY.get_room_state(data['room'])
                    print(ret)
                    print(state)
                    if TestRoom.State.VOTING == TestRoom.State(state):
                        await send_answers(data['room'])
                else:
                    await send_error(websocket, ret)
            if ClientServerMsgs(data['type']) == ClientServerMsgs.submit_vote:
                ret = GATEWAY.submit_data(data['room'], data['user'], data)
                if ret == InteractReturnCodes.SUCCESS:
                    ret, state, _ = GATEWAY.get_room_state(data['room'])
                    print(ret)
                    print(state)
                    if TestRoom.State.SHOWING_RESULTS == TestRoom.State(state):
                        await send_results(data['room'])
                        asyncio.ensure_future(start_next_round(data['room']))
                else:
                    await send_error(websocket, ret)  
        except websockets.exceptions.ConnectionClosed:
            await unregister_user(websocket)            



async def start():
    # Using 'await' inside an async function instead of run_until_complete
    start_server = await websockets.serve(counter, "0.0.0.0", 6969)
    # No need for run_forever here - asyncio.run will handle that
    
    # Keep the server running
    await asyncio.Future()  # This will run forever

asyncio.run(start())