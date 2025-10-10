.PHONY: build up down dev-up dev-down dev-build help env

PRODUCTION ?= api
DEV ?= dev

RED = \033[0;31m
GREEN = \033[0;32m
NC = \033[0m

help: ## Show this help message
	@echo "-------------------------------------"
	@echo "${GREEN}telegramBot_n8n - Available commands:${NC}"
	@echo "-------------------------------------"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

env: ## Create .env file from env.example
	@if [ -f .env ]; then \
		echo "${RED}.env file already exists!${NC}"; \
	else \
		echo "${GREEN}Creating .env file from env.example${NC}"; \
		cp env.example .env; \
	fi

dev-up: ## Start development mode
	docker compose --profile development up -d

dev-down: ## Stop development mode
	docker compose --profile development down

dev-build: ## Build images for development mode
	docker compose --profile development build

up: ## Start production mode
	docker compose --profile production up -d

down: ## Stop production mode
	docker compose --profile production down

build: ## Build images for production mode
	docker compose --profile production build
