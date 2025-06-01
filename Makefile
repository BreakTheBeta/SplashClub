.PHONY: server client test kill gen_types

client:
	cd client && yarn serve

server:
	python3 main.py

kill:
	sudo lsof -i tcp:6969 

test:
	uv run pytest

gen_types:
	pydantic2ts --module ./splash_club/contracts.py --output client/src/generated/sockets_types.ts



