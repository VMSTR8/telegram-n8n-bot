.PHONY: migrate upgrade downgrade init-db init

SERVICE = api

GREEN = \033[0;32m
NC = \033[0m

help: ## Показать справку по командам
	@echo "-------------------------------------"
	@echo "${GREEN}telegramBot_n8n - Доступные команды:${NC}"
	@echo "-------------------------------------"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

init: ## Инициализация aerich (запустить один раз)
	docker compose run --rm bot aerich init -t config.TORTOISE_ORM

init-db: ## Инициализация базы данных (запустить один раз)
	docker compose run --rm $(SERVICE) aerich init-db

migrate: ## Создание миграции
	docker compose run --rm $(SERVICE) aerich migrate

upgrade: ## Применение миграции
	docker compose run --rm $(SERVICE) aerich upgrade

downgrade: ## Откат миграции
	docker compose run --rm $(SERVICE) aerich downgrade

history: ## Просмотр истории миграций
	docker compose run --rm $(SERVICE) aerich history

inspectdb: ## Автоматическое создание моделей из существующей базы данных
	docker compose run --rm $(SERVICE) aerich inspectdb

dev-up: ## Запуск в режиме разработки
	docker compose --profile debug up -d

dev-down: ## Остановка режима разработки
	docker compose --profile debug down

prod-up: ## Запуск в продакшн режиме
	docker compose --profile production up -d

prod-down: ## Остановка продакшн режима
	docker compose --profile production down
