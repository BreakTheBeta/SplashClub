.PHONEY: server, client, test, kill

client:
	cd http/app && yarn start

server:
	python3 main.py

kill:
	sudo lsof -i tcp:6969 

test:
	python3 game_test.py


