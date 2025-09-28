# telegramBot_n8n

> **Внимание:** проект находится в стадии активной разработки.

## Описание

Этот репозиторий реализует Telegram-бота, интегрированного с автоматизациями n8n. Архитектура проекта построена с акцентом на модульность и удобство поддержки. Для API используется FastAPI, а логика бота, обработчики, модели и сервисы разделены по отдельным модулям.

## Стэк проекта
- **Язык:** [Python 3.13+](https://www.python.org/)
- **Фреймворк API:** [FastAPI](https://fastapi.tiangolo.com/)
- **Telegram Bot:** [aiogram](https://docs.aiogram.dev/)
- **ORM:** [Tortoise ORM](https://tortoise.github.io/toc.html)
- **Миграции:** [Aerich](https://tortoise.github.io/migration.html?h=aerich#)
- **Автоматизации:** [n8n](https://n8n.io/) (интеграция через сервисный слой)
- **Контейнеризация:** [Docker](https://www.docker.com/), [docker-compose](https://docs.docker.com/compose/)
- **Управление зависимостями:** [requirements.txt](https://pip.pypa.io/en/stable/user_guide/#requirements-files)
- **Конфигурация:** [pydantic-settings](https://docs.pydantic.dev/latest/integrations/pydantic_settings/), [.env](https://12factor.net/config)
- **Логирование:** стандартный [logging](https://docs.python.org/3/library/logging.html) с ротацией файлов
- **Управление командами:** [Makefile](https://www.gnu.org/software/make/manual/make.html)


## Архитектура и основные компоненты

- **main.py** — точка входа в приложение, инициализация и интеграция всех компонентов.
- **app/** — основная логика приложения:
    - `api_fastapi/` — эндпоинты FastAPI и связанная логика.
    - `bot_telegram/` — реализация Telegram-бота (`bot.py`), логирование и утилиты.
    - `handlers/` — обработчики команд и сообщений бота.
    - `models/` — модели данных (например, `user.py`).
    - `services/` — бизнес-логика и интеграции (n8n, внешние API).
    - `utils/` — вспомогательные функции.
    - `decorators/` — кастомные декораторы (например, для аутентификации, логирования).
- **config/** — управление конфигурацией (`settings.py` для переменных окружения).
- **Dockerfile** и **docker-compose.yml** — контейнеризация и оркестрация для разработки и деплоя.
- **requirements.txt** — зависимости Python.

## Быстрый старт

1. Создайте файл .env на основе примера env.example:
    ```sh
    make env
    ```
2. Заполните необходимые переменные окружения в `.env`.
3. Запустите проект при помощи Docker:
    ```sh
    make dev-up
    ```

> Справка со всеми доступными командами вызывается через команду **make help**

## Основные паттерны

- **Модульная структура:** каждый слой (API, бот, обработчики, сервисы) вынесен в отдельную директорию.
- **Централизованная конфигурация:** все настройки и секреты — в `config/settings.py`.
- **Логика бота:** в `app/bot_telegram/bot.py`, обработчики — в `app/handlers/`.
- **Сервисный слой:** интеграции и бизнес-логика — в `app/services/`.
- **Декораторы:** переиспользуемые декораторы — в `app/decorators/`.