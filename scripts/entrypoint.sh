#!/bin/bash
set -e

# Set timezone if TZ variable is provided
if [ -n "$TZ" ]; then
	export TZ=$TZ
	echo "Using timezone: $TZ"
else
	echo "TZ variable is not set, using system timezone"
fi

# 1. Инициализация базы и миграций
echo "Running aerich init-db..."
aerich init-db || true

# 2. Применение неприменённых миграций
echo "Running aerich migrate..."
if ! aerich migrate; then
	echo "[ERROR] Aerich migrate failed. Please check migrations manually (there may be conflicting or unnecessary files)."
	exit 1
fi

# 2.1. Применение всех миграций (upgrade)
echo "Running aerich upgrade..."
if ! aerich upgrade; then
	echo "[ERROR] Aerich upgrade failed. Please check migrations manually (there may be conflicting or unnecessary files)."
	exit 1
fi

# 3. Запуск основного приложения
echo "Starting main.py..."
python main.py
