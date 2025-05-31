.PHONY: server client client_old test kill gen_types

client_old:
	nvm use 23
	cd http/app && yarn start

client:
	cd client && yarn serve

server:
	python3 main.py

kill:
	sudo lsof -i tcp:6969 

test:
	python3 game_test.py

gen_types:
	pydantic2ts --module ./jill_box/contracts.py --output client/src/generated/sockets_types.ts

