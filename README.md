# Splash Club

<img src="./client/public/logo.png" alt="drawing" width="400"/>

This is a fork and major modernisation of the jill_box repo: https://github.com/axlan/jill_box. 

This demo game is similar to Fibbage, where players create fake answers to prompts and try to guess the real ones.

## Getting Started

### Prerequisites
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Node.js](https://nodejs.org/) version 23 and [Yarn](https://yarnpkg.com/)

### Installation

```bash
git clone git@github.com:BreakTheBeta/SplashClub.git
cd SplashClub
uv sync 
cd client
yarn install
cd ..
```

### Running the Game

1. **Start the backend server:**
   ```bash
   make run-server
   ```

2. **Start the frontend development server:**
   ```bash
   make run-client
   ```

3. **Open your browser and go to:** `http://localhost:5173` (or whatever port Vite shows)

4. **Check service status anytime:**
   ```bash
   make status
   ```

5. **Stop services when done:**
   ```bash
   make kill-server
   make kill-client
   ```


## Development Environment Management (Vibe Makefile)

This project uses a **"Vibe Makefile"** - a generic service management system that provides clean, minimal output by default with optional verbose mode.

### Prerequisites

Ensure you have `make` installed on your system.

### Key Features

- **Clean minimal output** - Shows just the command and startup logs
- **Automatic process tree killing** - Properly handles complex processes like yarn→vite
- **20-second startup display** - Shows real-time logs then auto-detaches
- **Fresh logs every start** - Overwrites old logs for clean viewing
- **Smart restart** - Automatically kills old processes before starting new ones
- **Verbose mode** - Add `V=1` for detailed output with emojis and debug info

### Service Configuration

Services are defined in the `Makefile`:

*   `SERVICE_NAMES`: A list of short names for your services (e.g., `server`, `client`).
*   `<name>_CMD`: The command to start the service (e.g., `python3 main.py`).
*   `<name>_WORKDIR`: The working directory for the command (defaults to `.` if not specified).
*   `<name>_STOP_CMD`: Optional graceful shutdown command (uses process tree kill by default).
*   `<name>_HEALTH`: Optional health check command for status monitoring.

All service-related files (PID files, log files) are stored in the `.services/` directory at the root of the project.

### Common Commands

*   **`make help`**: Displays a list of all available make targets and their descriptions.

*   **`make run-<service_name>`**: Starts the specified service in the background.
    *   Example: `make run-server`
    *   Shows: `Running: python3 main.py` + 20 seconds of startup logs
    *   Automatically kills old instances and starts fresh
    *   Use `make run-server V=1` for verbose output with detailed logging

*   **`make run-<service_name> ATTACH=1`**: Starts the specified service in the foreground.
    *   Example: `make run-client ATTACH=1`
    *   Useful for interactive debugging or seeing live output directly in your terminal.
    *   Press `Ctrl+C` to stop the service.

*   **`make status`**: Shows the current running status (running or not running) and PID for all defined services.

*   **`make log-<service_name>`**: Shows the full log file for the specified service.
    *   Example: `make log-server`

*   **`make kill-<service_name>`**: Stops the specified running service.
    *   Example: `make kill-server`
    *   Shows: `Process killed successfully`
    *   Use `make kill-server V=1` for detailed process tree killing output

### Other Useful Commands

*   **`make clean`**: Removes Python cache files (`*.pyc`) and the `.services/` directory.
*   **`make test`**: Runs Python tests using `uv run pytest`.
*   **`make gen_types`**: Generates TypeScript types from Pydantic models.

### Adding New Services

To add a new service:

1. Add to `SERVICE_NAMES`: `SERVICE_NAMES := server client newservice`
2. Define the command: `newservice_CMD := your-command-here`
3. Optional: Set working directory, stop command, or health check

Example:
```makefile
redis_CMD := redis-server
redis_STOP_CMD := redis-cli shutdown
redis_HEALTH := redis-cli ping
```

**Example Workflow:**

1.  Start the backend server: `make run-server`
2.  Start the frontend client: `make run-client`
3.  Check their status: `make status`
4.  View server logs: `make log-server`
5.  Stop the server: `make kill-server`


## Screenshots

![](./assets/login.png)
![](./assets/waiting.png)
![](./assets/question.png)

## Todo List

- [x] Disconnect/reconnect logic to stay in game
- [x] Clean up App.tsx
- [ ] Add sound effects and other assets
- [x] Add room owner privileges
