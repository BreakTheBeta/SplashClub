.PHONY: help status $(addprefix run-,$(SERVICE_NAMES)) $(addprefix kill-,$(SERVICE_NAMES)) $(addprefix log-,$(SERVICE_NAMES)) clean test gen_types kill-rogue-server

# Directory for PIDs and logs
SERVICE_BASE_DIR := .services
# Absolute path to service directory. $(CURDIR) is directory of current Makefile.
SERVICE_DIR_ABS := $(CURDIR)/$(SERVICE_BASE_DIR)

# List your services here:
SERVICE_NAMES := server client

# For each service, define:
#   <name>_CMD      := the command to launch it
#   <name>_WORKDIR  := directory to cd into before running (optional; default is .)
#
# Example:
server_CMD := python3 main.py
server_WORKDIR := .

client_CMD := yarn serve
client_WORKDIR := client

help:  ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo "========= Service Commands ========="
	@for srv in $(SERVICE_NAMES); do \
		printf "  \033[36m%-25s\033[0m %s\n" "run-$$srv" "Start/restart $$srv (background)"; \
		printf "  \033[36m%-25s\033[0m %s\n" "run-$$srv ATTACH=1" "Start $$srv in foreground"; \
		printf "  \033[36m%-25s\033[0m %s\n" "kill-$$srv" "Stop $$srv"; \
		printf "  \033[36m%-25s\033[0m %s\n" "log-$$srv" "Show logs for $$srv"; \
	done

# ---------------- run-<name> ----------------
run-%:  ## Start/restart <$*>. Use ATTACH=1 for foreground.
	@$(eval _NAME := $*)
	@$(eval _CMD  := $($*_CMD))
	@$(eval _WD   := $(or $($*_WORKDIR),.)) # Default to . if not set
	@$(eval _PIDF := $(SERVICE_DIR_ABS)/$(_NAME).pid)
	@$(eval _LOGF := $(SERVICE_DIR_ABS)/$(_NAME).log)

	@echo "--- Preparing to run $(_NAME) ---"
	@echo "  Command: $(_CMD)"
	@echo "  Working directory: $(_WD)"
	@echo "  PID file: $(_PIDF)"
	@echo "  Log file: $(_LOGF)"

	@if [ -z "$(_CMD)" ]; then \
		echo "❌ Error: $(_NAME)_CMD is undefined."; exit 1; \
	fi; \
	mkdir -p "$(SERVICE_DIR_ABS)"; \
	\
	echo "--- Stopping old process for $(_NAME) (if any) ---"; \
	if [ -f "$(_PIDF)" ]; then \
		_OLD_PID=$$(cat "$(_PIDF)" 2>/dev/null); \
		if [ -n "$$_OLD_PID" ] && kill -0 $$_OLD_PID 2>/dev/null; then \
			echo "🔄  Stopping old process $$_OLD_PID for $(_NAME)..."; \
			kill $$_OLD_PID; \
			sleep 0.5; \
			if kill -0 $$_OLD_PID 2>/dev/null; then \
				echo "⚠️  Old process $$_OLD_PID did not stop with SIGTERM. Sending SIGKILL..."; \
				kill -9 $$_OLD_PID; \
				sleep 0.5; \
			fi; \
			if kill -0 $$_OLD_PID 2>/dev/null; then \
				echo "❌ Error: Failed to stop old process $$_OLD_PID."; \
			else \
				echo "🛑  Old process $$_OLD_PID stopped."; \
			fi; \
		else \
			echo "ℹ️  Stale PID file found: $(_PIDF) (process $$_OLD_PID not running or PID missing). Removing."; \
		fi; \
		rm -f "$(_PIDF)"; \
	else \
		echo "ℹ️  No existing PID file found for $(_NAME)."; \
	fi; \
	\
	if [ "$(ATTACH)" = "1" ]; then \
		echo "--- Starting $(_NAME) in ATTACH mode (foreground) ---"; \
		cd "$(_WD)" && $(_CMD); \
		_EXIT_CODE=$$?; \
		echo "--- $(_NAME) (foreground) exited with code $$_EXIT_CODE ---"; \
		exit $$_EXIT_CODE; \
	else \
		echo "--- Starting $(_NAME) in DETACH mode (background) ---"; \
		( cd "$(_WD)" && nohup $(_CMD) >>"$(_LOGF)" 2>&1 & echo $$! >"$(_PIDF)" ); \
		_LAUNCH_EC=$$?; \
		if [ $$_LAUNCH_EC -ne 0 ]; then \
			echo "❌ Error: Failed to launch background subshell for $(_NAME). Shell exit code: $$_LAUNCH_EC"; \
			exit 1; \
		fi; \
		echo "⏳  Waiting for process to stabilize (1s)..."; \
		sleep 1; \
		_NEW_PID=$$(cat "$(_PIDF)" 2>/dev/null); \
		if [ -n "$$_NEW_PID" ] && kill -0 $$_NEW_PID 2>/dev/null; then \
			echo "✅  $(_NAME) is RUNNING (PID $$_NEW_PID)."; \
		else \
			if [ -z "$$_NEW_PID" ]; then \
				echo "❌ Error: $(_NAME) FAILED to start (PID file $(_PIDF) not created or empty)."; \
			else \
				echo "❌ Error: $(_NAME) FAILED to start or EXITED QUICKLY (PID from file: $$_NEW_PID)."; \
			fi; \
			echo "   Check logs for more details."; \
		fi; \
		echo "--- Log Information for $(_NAME) ---"; \
		if [ -f "$(_LOGF)" ]; then \
			if [ -s "$(_LOGF)" ]; then \
				echo "   Showing first 20 lines of log: $(_LOGF)"; \
				head -n 20 "$(_LOGF)"; \
			else \
				echo "   Log file $(_LOGF) exists but is EMPTY."; \
			fi; \
		else \
			echo "   Log file $(_LOGF) does NOT exist."; \
			echo "   (This may be normal if the command hasn't produced output yet or failed before logging)."; \
		fi; \
		echo "--- End of $(_NAME) run ---"; \
	fi

# ---------------- kill-<name> --------------
kill-%:  ## Stop <$*>
	@$(eval _NAME := $*)
	@$(eval _PIDF := $(SERVICE_DIR_ABS)/$(_NAME).pid)
	@echo "--- Attempting to kill $(_NAME) ---"
	@if [ -f "$(_PIDF)" ]; then \
		_PID_TO_KILL=$$(cat "$(_PIDF)" 2>/dev/null); \
		if [ -n "$$_PID_TO_KILL" ] && kill -0 $$_PID_TO_KILL 2>/dev/null; then \
			echo "🛑  Killing $(_NAME) (pid $$_PID_TO_KILL)..."; \
			kill $$_PID_TO_KILL; \
			sleep 0.5; \
			if kill -0 $$_PID_TO_KILL 2>/dev/null; then \
				echo "⚠️  Process $$_PID_TO_KILL for $(_NAME) did not stop with SIGTERM. Sending SIGKILL..."; \
				kill -9 $$_PID_TO_KILL; \
				sleep 0.5; \
			fi; \
			if kill -0 $$_PID_TO_KILL 2>/dev/null; then \
				echo "❌ Error: Failed to kill process $$_PID_TO_KILL for $(_NAME)."; \
			else \
				echo "✅  Process $$_PID_TO_KILL for $(_NAME) stopped."; \
				rm -f "$(_PIDF)"; \
			fi; \
		else \
			echo "ℹ️  $(_NAME) not running (stale PID file: $(_PIDF) with PID $$_PID_TO_KILL, or PID missing). Removing PID file."; \
			rm -f "$(_PIDF)"; \
		fi; \
	else \
		echo "ℹ️  $(_NAME) not running (no PID file found at $(_PIDF))."; \
	fi

# ---------------- log-<name> ---------------
log-%:  ## Show full log of <$*>
	@$(eval _NAME := $*)
	@$(eval _LOGF := $(SERVICE_DIR_ABS)/$(_NAME).log)
	@echo "--- Displaying log for $(_NAME) from $(_LOGF) ---"
	@if [ -f "$(_LOGF)" ]; then \
		if [ -s "$(_LOGF)" ]; then \
			cat "$(_LOGF)"; \
		else \
			echo "ℹ️  Log file exists but is empty for $(_NAME)."; \
		fi; \
	else \
		echo "ℹ️  No log file found for $(_NAME) at $(_LOGF)."; \
	fi

# ---------------- status -------------------
status:  ## Show status of all services
	@echo "--- Service Status ---"
	@for srv in $(SERVICE_NAMES); do \
		_PIDF="$(SERVICE_DIR_ABS)/$$srv.pid"; \
		if [ -f "$$_PIDF" ]; then \
			_CURRENT_PID=$$(cat "$$_PIDF" 2>/dev/null); \
			if [ -n "$$_CURRENT_PID" ] && kill -0 $$_CURRENT_PID 2>/dev/null; then \
				printf "  \033[32m●\033[0m %-12s running (pid %s)\n" "$$srv:" "$$_CURRENT_PID"; \
			else \
				printf "  \033[31m◌\033[0m %-12s not running (stale pid file: %s, pid %s)\n" "$$srv:" "$$_PIDF" "$$_CURRENT_PID"; \
			fi; \
		else \
			printf "  \033[31m◌\033[0m %-12s not running (no pid file)\n" "$$srv:"; \
		fi; \
	done

# Example other targets:
gen_types:  ## Generate TypeScript types from Pydantic models
	pydantic2ts --module ./splash_club/contracts.py --output client/src/generated/sockets_types.ts

clean:  ## Clean up Python cache files and service files
	@echo "--- Cleaning up ---"
	find . -name '*.pyc' -delete -print
	@if [ -d "$(SERVICE_DIR_ABS)" ]; then \
		echo "Removing $(SERVICE_DIR_ABS)..."; \
		rm -rf "$(SERVICE_DIR_ABS)"; \
	else \
		echo "$(SERVICE_DIR_ABS) not found, nothing to remove."; \
	fi
	@echo "--- Cleanup complete ---"

kill-rogue-server:  ## Find and kill any rogue server processes running on port 6969
	@echo "--- Finding rogue server processes on port 6969 ---"
	@_PIDS=$$(lsof -ti :6969 2>/dev/null || true); \
	if [ -n "$$_PIDS" ]; then \
		echo "🔍  Found processes using port 6969: $$_PIDS"; \
		for _PID in $$_PIDS; do \
			_PROCESS_INFO=$$(ps -p $$_PID -o pid,ppid,command 2>/dev/null || echo "Process $$_PID not found"); \
			echo "📋  Process details: $$_PROCESS_INFO"; \
			if kill -0 $$_PID 2>/dev/null; then \
				echo "🛑  Killing rogue process $$_PID..."; \
				kill $$_PID; \
				sleep 0.5; \
				if kill -0 $$_PID 2>/dev/null; then \
					echo "⚠️   Process $$_PID did not stop with SIGTERM. Sending SIGKILL..."; \
					kill -9 $$_PID; \
					sleep 0.5; \
				fi; \
				if kill -0 $$_PID 2>/dev/null; then \
					echo "❌  Failed to kill process $$_PID"; \
				else \
					echo "✅  Successfully killed process $$_PID"; \
				fi; \
			else \
				echo "ℹ️   Process $$_PID already dead"; \
			fi; \
		done; \
	else \
		echo "✅  No processes found using port 6969"; \
	fi; \
	echo "--- Rogue server cleanup complete ---"

test:  ## Run Python tests using uv
	uv run pytest
