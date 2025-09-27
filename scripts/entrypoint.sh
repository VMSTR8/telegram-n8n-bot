#!/bin/bash
set -e

# Установка часового пояса из переменной окружения
if [ -n "$TZ" ]; then
	export TZ=$TZ
	echo "Используется часовой пояс: $TZ"
else
	echo "Переменная TZ не задана, используется системный часовой пояс"
fi

# 1. Инициализация базы и миграций
echo "Выполняется aerich init-db..."
aerich init-db || true

# 2. Применение неприменённых миграций
echo "Выполняется aerich migrate (применение неприменённых миграций)..."
aerich migrate || true

# 3. Запуск основного приложения
echo "Запуск main.py..."
python main.py
