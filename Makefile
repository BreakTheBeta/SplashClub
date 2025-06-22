.PHONY: help client server test kill gen_types clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

client:  ## Run the frontend client
	cd client && yarn serve

server:  ## Run the backend server
	python3 main.py

kill:  ## Kill server process on port 6969
	sudo lsof -i tcp:6969 

test:  ## Run Python tests using uv
	uv run pytest

gen_types:  ## Generate TypeScript types from Pydantic models
	pydantic2ts --module ./splash_club/contracts.py --output client/src/generated/sockets_types.ts

clean:  ## Clean up Python cache files
	find . -name '*.pyc' -delete

