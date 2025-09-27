.PHONY: migrate upgrade downgrade init-db init

PRODUCTION ?= api
DEV ?= dev

RED = \033[0;31m
GREEN = \033[0;32m
NC = \033[0m

help: ## Показать справку по командам
	@echo "-------------------------------------"
	@echo "${GREEN}telegramBot_n8n - Доступные команды:${NC}"
	@echo "-------------------------------------"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

env: ## Создание файла .env из env.example
	@if [ -f .env ]; then \
		echo "${RED}.env файл уже существует!${NC}"; \
	else \
		echo "${GREEN}Создание .env файла из env.example${NC}"; \
		cp env.example .env; \
	fi

dev-up: ## Запуск в режиме разработки
	docker compose --profile development up -d

dev-down: ## Остановка режима разработки
	docker compose --profile development down

dev-build: ## Сборка образов для разработки
	docker compose --profile development build

prod-up: ## Запуск в продакшн режиме
	docker compose --profile production up -d

prod-down: ## Остановка продакшн режима
	docker compose --profile production down

prod-build: ## Сборка образов для продакшн режима
	docker compose --profile production build
