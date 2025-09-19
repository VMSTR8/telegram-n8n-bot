.PHONY: migrate upgrade downgrade init-db init
SERVICE = понятия_не_имею_как_я_назову_сервис_пусть_будет_пока_так

init:
	docker compose run --rm bot aerich init -t config.TORTOISE_ORM

init-db:
	docker compose run --rm $(SERVICE) aerich init-db

migrate:
	docker compose run --rm $(SERVICE) aerich migrate

upgrade:
	docker compose run --rm $(SERVICE) aerich upgrade

downgrade:
	docker compose run --rm $(SERVICE) aerich downgrade

history:
	docker compose run --rm $(SERVICE) aerich history

inspectdb:
	docker compose run --rm $(SERVICE) aerich inspectdb
