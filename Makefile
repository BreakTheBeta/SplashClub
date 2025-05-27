.PHONY: server client client_old test kill

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


