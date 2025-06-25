# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands (Vibe Makefile)

The project uses a **"Vibe Makefile"** - a generic service management system with clean output by default and verbose mode when needed.

### Designed for Autonomous Agents
This Vibe Makefile is specifically designed to make it easier for vibe coding agents, AI assistants, and other autonomous agents to handle starting and stopping multiple services without blocking operations. Key benefits for agents:
- **Non-blocking service management** - Services run in background by default, agents don't get stuck waiting
- **Easy log access for debugging** - Simple `make log-<service>` commands to get service logs
- **Clear status reporting** - `make status` shows all services at once with clear indicators  
- **Predictable output format** - Consistent formatting makes it easy for agents to parse results
- **Automatic cleanup** - Handles stale processes and complex process trees automatically
- **No manual PID tracking** - Agents don't need to manage process IDs or complex process hierarchies

### Core Services
- `make run-server` - Start Python WebSocket server (shows command + 20s startup logs)
- `make run-client` - Start React dev server (shows command + 20s startup logs)
- `make status` - Check status of all services
- `make kill-server` / `make kill-client` - Stop services (shows "Process killed successfully")
- `make log-server` / `make log-client` - View service logs

### Verbose Mode
Add `V=1` to any command for detailed output with emojis and debug info:
- `make run-server V=1` - Full verbose startup with detailed logging
- `make kill-server V=1` - Detailed process tree killing with debug output
- `make status V=1` - Enhanced status with health checks (if configured)

### Development Workflow
- `make run-server ATTACH=1` - Run server in foreground for debugging
- `make run-client ATTACH=1` - Run client in foreground for debugging
- `make test` - Run Python tests with `uv run pytest`
- `make clean` - Clean Python cache and service files
- `make gen_types` - Generate TypeScript types from Pydantic models

### Vibe Makefile Features
- **Clean minimal output** by default - just shows command and logs
- **Automatic process tree killing** - properly handles yarn→vite and other complex processes
- **20-second startup display** - shows real-time logs then auto-detaches
- **Fresh logs every start** - overwrites old logs for clean startup viewing
- **Generic service system** - easy to add new services without hardcoding
- **Smart restart** - automatically kills old processes before starting new ones

### Adding New Services
To add a new service to the Vibe Makefile:

1. **Add to SERVICE_NAMES**: `SERVICE_NAMES := server client newservice`
2. **Define the command**: `newservice_CMD := your-command-here`
3. **Optional settings**:
   - `newservice_WORKDIR := ./path/to/workdir` (defaults to current directory)
   - `newservice_STOP_CMD := graceful-shutdown-command` (uses process tree kill by default)
   - `newservice_HEALTH := health-check-command` (for status monitoring)

**Examples:**
```makefile
# Database service
redis_CMD := redis-server
redis_STOP_CMD := redis-cli shutdown
redis_HEALTH := redis-cli ping

# Python API with virtual environment
api_CMD := ./venv/bin/python app.py
api_WORKDIR := ./backend
api_HEALTH := curl -f localhost:5000/ping

# Simple background worker
worker_CMD := python worker.py
worker_WORKDIR := ./scripts
```

Once defined, all standard commands work automatically:
- `make run-newservice` / `make run-newservice V=1`
- `make kill-newservice` / `make kill-newservice V=1`
- `make log-newservice`

### Frontend Commands (from client/ directory)
- `yarn dev` - Development server
- `yarn serve` - Development server with external access
- `yarn build` - Build production bundle
- `yarn lint` - ESLint code checking

### Important Service Management Rules
- **NEVER start the server or client directly** - Always use the provided Makefile commands (`make run-server`, `make run-client`)
- The Makefile handles proper service management, process tracking, and cleanup
- Direct execution bypasses the project's service management system

### Vibe Makefile Configuration
- **Startup timeout**: Configurable via `STARTUP_TIMEOUT` variable in Makefile (default: 20 seconds)
- Services show real-time logs during startup, then auto-detach after the timeout
- To change timeout: modify `STARTUP_TIMEOUT := 20` to desired seconds (e.g., `STARTUP_TIMEOUT := 10`)

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