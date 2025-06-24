.PHONY: help status $(addprefix run-,$(SERVICE_NAMES)) $(addprefix kill-,$(SERVICE_NAMES)) $(addprefix log-,$(SERVICE_NAMES)) clean test gen_types

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
		printf "  \033[36m%-25s\033[0m %s\n" "run-$$srv V=1" "Start $$srv with verbose output"; \
		printf "  \033[36m%-25s\033[0m %s\n" "kill-$$srv" "Stop $$srv"; \
		printf "  \033[36m%-25s\033[0m %s\n" "kill-$$srv V=1" "Stop $$srv with verbose output"; \
		printf "  \033[36m%-25s\033[0m %s\n" "log-$$srv" "Show logs for $$srv"; \
	done

# ---------------- run-<name> ----------------
run-%:  ## Start/restart <$*>. Use ATTACH=1 for foreground, V=1 for verbose.
	@$(eval _NAME := $*)
	@$(eval _CMD  := $($*_CMD))
	@$(eval _WD   := $(or $($*_WORKDIR),.)) # Default to . if not set
	@$(eval _PIDF := $(SERVICE_DIR_ABS)/$(_NAME).pid)
	@$(eval _LOGF := $(SERVICE_DIR_ABS)/$(_NAME).log)

	@if [ "$(V)" = "1" ]; then \
		echo "--- Preparing to run $(_NAME) ---"; \
		echo "  Command: $(_CMD)"; \
		echo "  Working directory: $(_WD)"; \
		echo "  PID file: $(_PIDF)"; \
		echo "  Log file: $(_LOGF)"; \
	else \
		echo "Running: $(_CMD)"; \
	fi

	@if [ -z "$(_CMD)" ]; then \
		echo "❌ Error: $(_NAME)_CMD is undefined."; exit 1; \
	fi; \
	mkdir -p "$(SERVICE_DIR_ABS)"; \
	\
	if [ "$(V)" = "1" ]; then \
		echo "--- Stopping old process for $(_NAME) (if any) ---"; \
	fi; \
	if [ -f "$(_PIDF)" ]; then \
		_OLD_PID=$$(cat "$(_PIDF)" 2>/dev/null); \
		if [ -n "$$_OLD_PID" ] && kill -0 $$_OLD_PID 2>/dev/null; then \
			if [ "$(V)" = "1" ]; then \
				echo "🔄  Stopping old process $$_OLD_PID for $(_NAME)..."; \
				echo "🔍  Killing process tree for PID $$_OLD_PID..."; \
			fi; \
			_CHILD_PIDS=$$(pgrep -P $$_OLD_PID 2>/dev/null || true); \
			if [ -n "$$_CHILD_PIDS" ]; then \
				if [ "$(V)" = "1" ]; then \
					echo "🔍  Found child processes: $$_CHILD_PIDS"; \
				fi; \
				for _CHILD_PID in $$_CHILD_PIDS; do \
					if [ "$(V)" = "1" ]; then \
						echo "🔍  Killing child process $$_CHILD_PID..."; \
					fi; \
					kill $$_CHILD_PID 2>/dev/null || true; \
					_GRANDCHILD_PIDS=$$(pgrep -P $$_CHILD_PID 2>/dev/null || true); \
					if [ -n "$$_GRANDCHILD_PIDS" ]; then \
						if [ "$(V)" = "1" ]; then \
							echo "🔍  Found grandchild processes: $$_GRANDCHILD_PIDS"; \
						fi; \
						for _GRANDCHILD_PID in $$_GRANDCHILD_PIDS; do \
							if [ "$(V)" = "1" ]; then \
								echo "🔍  Killing grandchild process $$_GRANDCHILD_PID..."; \
							fi; \
							kill $$_GRANDCHILD_PID 2>/dev/null || true; \
						done; \
					fi; \
				done; \
			else \
				if [ "$(V)" = "1" ]; then \
					echo "🔍  No child processes found for PID $$_OLD_PID"; \
				fi; \
			fi; \
			kill $$_OLD_PID 2>/dev/null || true; \
			sleep 0.5; \
			if kill -0 $$_OLD_PID 2>/dev/null; then \
				if [ "$(V)" = "1" ]; then \
					echo "⚠️  Old process $$_OLD_PID did not stop with SIGTERM. Sending SIGKILL..."; \
				fi; \
				kill -9 $$_OLD_PID 2>/dev/null || true; \
				sleep 0.5; \
			fi; \
			if kill -0 $$_OLD_PID 2>/dev/null; then \
				if [ "$(V)" = "1" ]; then \
					echo "❌ Error: Failed to stop old process $$_OLD_PID."; \
				fi; \
			else \
				if [ "$(V)" = "1" ]; then \
					echo "🛑  Old process $$_OLD_PID stopped."; \
				fi; \
			fi; \
		else \
			if [ "$(V)" = "1" ]; then \
				echo "ℹ️  Stale PID file found: $(_PIDF) (process $$_OLD_PID not running or PID missing). Removing."; \
			fi; \
		fi; \
		rm -f "$(_PIDF)"; \
	else \
		if [ "$(V)" = "1" ]; then \
			echo "ℹ️  No existing PID file found for $(_NAME)."; \
		fi; \
	fi; \
	\
	if [ "$(ATTACH)" = "1" ]; then \
		if [ "$(V)" = "1" ]; then \
			echo "--- Starting $(_NAME) in ATTACH mode (foreground) ---"; \
		fi; \
		cd "$(_WD)" && $(_CMD); \
		_EXIT_CODE=$$?; \
		if [ "$(V)" = "1" ]; then \
			echo "--- $(_NAME) (foreground) exited with code $$_EXIT_CODE ---"; \
		fi; \
		exit $$_EXIT_CODE; \
	else \
		if [ "$(V)" = "1" ]; then \
			echo "--- Starting $(_NAME) in DETACH mode (background) ---"; \
		fi; \
		( cd "$(_WD)" && nohup $(_CMD) >"$(_LOGF)" 2>&1 & echo $$! >"$(_PIDF)" ); \
		_LAUNCH_EC=$$?; \
		if [ $$_LAUNCH_EC -ne 0 ]; then \
			echo "❌ Error: Failed to launch $(_NAME). Exit code: $$_LAUNCH_EC"; \
			exit 1; \
		fi; \
		if [ "$(V)" = "1" ]; then \
			echo "⏳  Waiting for process to stabilize (2s)..."; \
		fi; \
		sleep 2; \
		_SHELL_PID=$$(cat "$(_PIDF)" 2>/dev/null); \
		if [ -n "$$_SHELL_PID" ]; then \
			_ACTUAL_PID=$$(pgrep -P $$_SHELL_PID 2>/dev/null | head -1); \
			if [ -n "$$_ACTUAL_PID" ]; then \
				echo $$_ACTUAL_PID >"$(_PIDF)"; \
				_NEW_PID=$$_ACTUAL_PID; \
			else \
				_NEW_PID=$$_SHELL_PID; \
			fi; \
		else \
			_NEW_PID=""; \
		fi; \
		if [ -n "$$_NEW_PID" ] && kill -0 $$_NEW_PID 2>/dev/null; then \
			if [ "$(V)" = "1" ]; then \
				echo "✅  $(_NAME) is RUNNING (PID $$_NEW_PID)."; \
				echo "📋  Showing startup output for 20 seconds, then detaching..."; \
				echo "────────────────────────────────────────────────────────"; \
			fi; \
		else \
			echo "❌ Error: $(_NAME) FAILED to start"; \
			exit 1; \
		fi; \
		pkill -f "tail -f.*$(_LOGF)" 2>/dev/null || true; \
		( \
			if command -v timeout >/dev/null 2>&1; then \
				timeout 20 tail -f "$(_LOGF)" 2>/dev/null; \
			elif command -v gtimeout >/dev/null 2>&1; then \
				gtimeout 20 tail -f "$(_LOGF)" 2>/dev/null; \
			else \
				tail -f "$(_LOGF)" 2>/dev/null & \
				_TAIL_PID=$$!; \
				sleep 20; \
				kill $$_TAIL_PID 2>/dev/null; \
				wait $$_TAIL_PID 2>/dev/null; \
			fi; \
		) 2>/dev/null || true; \
		pkill -f "tail -f.*$(_LOGF)" 2>/dev/null || true; \
		if [ "$(V)" = "1" ]; then \
			echo ""; \
			echo "────────────────────────────────────────────────────────"; \
			echo "✅  $(_NAME) is running in background (PID $$_NEW_PID)"; \
			echo "📄  Full logs: make log-$(_NAME)"; \
			echo "🛑  Stop service: make kill-$(_NAME)"; \
		fi; \
	fi

# ---------------- kill-<name> --------------
kill-%:  ## Stop <$*>. Use V=1 for verbose.
	@$(eval _NAME := $*)
	@$(eval _PIDF := $(SERVICE_DIR_ABS)/$(_NAME).pid)
	@if [ "$(V)" = "1" ]; then \
		echo "--- Attempting to kill $(_NAME) ---"; \
	fi
	@if [ -f "$(_PIDF)" ]; then \
		_PID_TO_KILL=$$(cat "$(_PIDF)" 2>/dev/null); \
		if [ -n "$$_PID_TO_KILL" ] && kill -0 $$_PID_TO_KILL 2>/dev/null; then \
			if [ "$(V)" = "1" ]; then \
				echo "🛑  Killing $(_NAME) (pid $$_PID_TO_KILL)..."; \
				echo "🔍  Killing process tree for PID $$_PID_TO_KILL..."; \
			fi; \
			_CHILD_PIDS=$$(pgrep -P $$_PID_TO_KILL 2>/dev/null || true); \
			if [ -n "$$_CHILD_PIDS" ]; then \
				if [ "$(V)" = "1" ]; then \
					echo "🔍  Found child processes: $$_CHILD_PIDS"; \
				fi; \
				for _CHILD_PID in $$_CHILD_PIDS; do \
					if [ "$(V)" = "1" ]; then \
						echo "🔍  Killing child process $$_CHILD_PID..."; \
					fi; \
					kill $$_CHILD_PID 2>/dev/null || true; \
					_GRANDCHILD_PIDS=$$(pgrep -P $$_CHILD_PID 2>/dev/null || true); \
					if [ -n "$$_GRANDCHILD_PIDS" ]; then \
						if [ "$(V)" = "1" ]; then \
							echo "🔍  Found grandchild processes: $$_GRANDCHILD_PIDS"; \
						fi; \
						for _GRANDCHILD_PID in $$_GRANDCHILD_PIDS; do \
							if [ "$(V)" = "1" ]; then \
								echo "🔍  Killing grandchild process $$_GRANDCHILD_PID..."; \
							fi; \
							kill $$_GRANDCHILD_PID 2>/dev/null || true; \
						done; \
					fi; \
				done; \
			else \
				if [ "$(V)" = "1" ]; then \
					echo "🔍  No child processes found for PID $$_PID_TO_KILL"; \
				fi; \
			fi; \
			kill $$_PID_TO_KILL 2>/dev/null || true; \
			sleep 0.5; \
			if kill -0 $$_PID_TO_KILL 2>/dev/null; then \
				if [ "$(V)" = "1" ]; then \
					echo "⚠️  Process $$_PID_TO_KILL for $(_NAME) did not stop with SIGTERM. Sending SIGKILL..."; \
				fi; \
				kill -9 $$_PID_TO_KILL 2>/dev/null || true; \
				sleep 0.5; \
			fi; \
			if kill -0 $$_PID_TO_KILL 2>/dev/null; then \
				echo "❌ Error: Failed to kill process $$_PID_TO_KILL for $(_NAME)."; \
			fi; \
			rm -f "$(_PIDF)"; \
			echo "Process killed successfully"; \
		else \
			if [ "$(V)" = "1" ]; then \
				echo "ℹ️  $(_NAME) not running (stale PID file: $(_PIDF) with PID $$_PID_TO_KILL, or PID missing). Removing PID file."; \
			fi; \
			rm -f "$(_PIDF)"; \
		fi; \
	else \
		if [ "$(V)" = "1" ]; then \
			echo "ℹ️  $(_NAME) not running (no PID file found at $(_PIDF))."; \
		fi; \
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
	@echo "Killing any orphaned tail processes..."
	@pkill -f "tail -f.*\.services.*\.log" 2>/dev/null || true
	@if [ -d "$(SERVICE_DIR_ABS)" ]; then \
		echo "Removing $(SERVICE_DIR_ABS)..."; \
		rm -rf "$(SERVICE_DIR_ABS)"; \
	else \
		echo "$(SERVICE_DIR_ABS) not found, nothing to remove."; \
	fi
	@echo "--- Cleanup complete ---"


test:  ## Run Python tests using uv
	uv run pytest
