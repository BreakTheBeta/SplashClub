.PHONEY: server, client

client:
	cd http/app && yarn start

server:
	python3 main.py
