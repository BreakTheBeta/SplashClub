# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Core Services
- `make run-server` - Start Python WebSocket server (background)
- `make run-client` - Start React dev server (background)
- `make status` - Check status of all services
- `make kill-server` / `make kill-client` - Stop services
- `make log-server` / `make log-client` - View service logs

### Development Workflow
- `make run-server ATTACH=1` - Run server in foreground for debugging
- `make run-client ATTACH=1` - Run client in foreground for debugging
- `make test` - Run Python tests with `uv run pytest`
- `make clean` - Clean Python cache and service files
- `make gen_types` - Generate TypeScript types from Pydantic models

### Frontend Commands (from client/ directory)
- `yarn dev` - Development server
- `yarn serve` - Development server with external access
- `yarn build` - Build production bundle
- `yarn lint` - ESLint code checking

### Important Service Management Rules
- **NEVER start the server or client directly** - Always use the provided Makefile commands (`make run-server`, `make run-client`)
- The Makefile handles proper service management, process tracking, and cleanup
- Direct execution bypasses the project's service management system

## Architecture Overview

### Backend (Python)
The server is built as an async WebSocket application with clean separation of concerns:

- **main.py**: Entry point that starts the WebSocket server on port 6969
- **websocket_server.py**: Core WebSocket server handling connections and message routing
- **message_router.py**: Routes incoming messages to appropriate handlers
- **connection_manager.py**: Manages WebSocket connections and user sessions
- **game_state_manager.py**: Handles game state transitions and room management
- **game.py**: Contains game logic (GameGateway class)
- **contracts.py**: Pydantic models defining message contracts between client/server
- **handlers/**: Specific message handlers for different game actions

### Frontend (React + TypeScript)
React SPA with WebSocket communication:

- **App.tsx**: Router setup with room-based URLs
- **components/GameApp.tsx**: Main game component managing state and WebSocket connection
- **hooks/useGameWebSocket.ts**: WebSocket connection management with auto-reconnect
- **containers/**: Page components (Login, Waiting, Prompt, Vote, Results)
- **generated/sockets_types.ts**: Auto-generated TypeScript types from Python Pydantic models
- **theme/**: Theme system with context provider

### Key Design Patterns
- **Message-based architecture**: All client-server communication via typed JSON messages
- **State synchronization**: Server manages authoritative game state, clients receive updates
- **Reconnection handling**: Clients can rejoin rooms after disconnection using stored user IDs
- **Type safety**: Shared message contracts ensure type safety across Python/TypeScript boundary

### Data Flow
1. Client sends typed messages (contracts.py) via WebSocket
2. Server routes messages through MessageRouter to specific handlers
3. Handlers update game state and broadcast updates to room participants
4. Client receives state updates and renders appropriate UI components

## Testing
- Backend tests in `tests/` directory using pytest
- Test files: `test_websocket_server.py`, `test_prompt_game.py`, `test_rejoin_sync.py`
- Run with `make test` or `uv run pytest`

## Type Generation with Pydantic
The project maintains type safety between Python backend and TypeScript frontend using Pydantic models:

### Dependencies
- `pydantic>=2.11.4` - For Python model validation
- `pydantic-to-typescript>=2.0.0` - For TypeScript generation

### Workflow
1. Define message contracts in `splash_club/contracts.py` using Pydantic models
2. Run `make gen_types` to generate TypeScript interfaces
3. Command: `pydantic2ts --module ./splash_club/contracts.py --output client/src/generated/sockets_types.ts`
4. Generated types are automatically imported in React components

### Important Notes
- **Always regenerate types** after modifying Pydantic models in `contracts.py`
- Generated file includes ESLint/TSLint disable comments - don't edit manually
- Union types (IncomingMessage/OutgoingMessage) provide message discrimination
- Type generation preserves field descriptions as JSDoc comments

## WebSocket Implementation
The project uses specific WebSocket library versions that affect usage patterns:

### Backend Dependencies  
- `websockets>=15.0.1` - Modern async WebSocket library
- Uses `websockets.ServerConnection` type for connections
- Connection handling: `async with websockets.serve(handler, host, port)`
- Message iteration: `async for message_str in websocket:`

### Key WebSocket Usage Patterns
- **Connection lifecycle**: Handle in `async def handle_connection(websocket: websockets.ServerConnection)`
- **Message sending**: Use `await websocket.send(message_json)` 
- **Error handling**: Catch `websockets.exceptions.ConnectionClosedOK` and `ConnectionClosedError`
- **Safe sending**: Use `safe_websocket_send()` utility to handle connection failures

### Version-Specific Notes
- WebSocket 15.x uses different exception handling than older versions
- `ServerConnection` type annotation is crucial for proper typing
- Modern async iteration pattern (`async for`) is preferred over manual polling