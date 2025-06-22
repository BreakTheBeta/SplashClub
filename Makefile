.PHONY: help status $(addprefix run-,$(SERVICE_NAMES)) $(addprefix kill-,$(SERVICE_NAMES)) $(addprefix log-,$(SERVICE_NAMES))

# Directory for PIDs and logs
SERVICE_DIR := .services

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
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo "========= Service Commands ========="
	@for srv in $(SERVICE_NAMES); do \
		printf "  %-25s %s\n" "run-$$srv" "Start/restart $$srv (background)"; \
		printf "  %-25s %s\n" "run-$$srv ATTACH=1" "Start $$srv in foreground"; \
		printf "  %-25s %s\n" "kill-$$srv" "Stop $$srv"; \
		printf "  %-25s %s\n" "log-$$srv" "Show logs for $$srv"; \
	done

# Pattern to start/restart a service.
# Use “ATTACH=1” to run in foreground attached mode; by default it detaches and shows first 20s of logs.
run-%:  ## Start (or restart) the <service> in background (or foreground if ATTACH=1)
	$(eval CMD := $($*_CMD))
	$(eval WD := $($*_WORKDIR))
	@if [ -z "$(CMD)" ]; then \
		echo "Error: no command defined for service '$*'. Define $*_CMD."; exit 1; \
	fi
	@mkdir -p $(SERVICE_DIR)
	@PIDFILE=$(SERVICE_DIR)/$*.pid; LOGFILE=$(SERVICE_DIR)/$*.log; \
	if [ -f $$PIDFILE ] && kill -0 $$(cat $$PIDFILE) 2>/dev/null; then \
		echo "Stopping running $*…"; \
		kill $$(cat $$PIDFILE) && rm -f $$PIDFILE; \
		sleep 1; \
	fi; \
	echo "Starting $* $(if $(ATTACH),in foreground,as background service)…"; \
	if [ -n "$(ATTACH)" ]; then \
		# run in foreground, but still append to log
		cd $(WD) && \
		( $(CMD) 2>&1 | tee -a ../$(LOGFILE) ); \
	else \
		# detach
		cd $(WD) && \
		nohup $(CMD) >>../$(LOGFILE) 2>&1 & echo $$! >$$PIDFILE; \
		# show up to 20s of logs in real time
		echo "---- Showing up to 20 seconds of logs: ----"; \
		timeout 20s tail -n +1 -f ../$$LOGFILE || true; \
		echo "(Detached. Use 'make log-$*' to see full logs.)"; \
	fi

# Pattern to kill a service.
kill-%:  ## Kill the running <service>
	@PIDFILE=$(SERVICE_DIR)/$*.pid; \
	if [ -f $$PIDFILE ] && kill -0 $$(cat $$PIDFILE) 2>/dev/null; then \
		echo "Killing $*…"; \
		kill $$(cat $$PIDFILE); rm -f $$PIDFILE; \
	else \
		echo "$* not running."; \
	fi

# Pattern to show logs for a service.
log-%:  ## Show all logs from <service> (can pipe to head/tail)
	@LOGFILE=$(SERVICE_DIR)/$*.log; \
	if [ -f $$LOGFILE ]; then \
		cat $$LOGFILE; \
	else \
		echo "No logs for $* yet."; \
	fi

# Global status: list each service and whether it’s running.
status:  ## Show status of all services
	@echo "Service status:"; \
	for srv in $(SERVICE_NAMES); do \
		PIDFILE=$(SERVICE_DIR)/$$srv.pid; \
		if [ -f $$PIDFILE ] && kill -0 $$(cat $$PIDFILE) 2>/dev/null; then \
			echo "  $$srv: running (pid $$(cat $$PIDFILE))"; \
		else \
			echo "  $$srv: not running"; \
		fi; \
	done

# Example other targets:
gen_types:  ## Generate TypeScript types from Pydantic models
	pydantic2ts --module ./splash_club/contracts.py --output client/src/generated/sockets_types.ts

clean:  ## Clean up Python cache files
	find . -name '*.pyc' -delete

test:  ## Run Python tests using uv
	uv run pytest

