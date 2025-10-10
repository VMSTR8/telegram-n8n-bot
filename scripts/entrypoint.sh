#!/bin/bash
set -e

# Set timezone if TZ variable is provided
if [ -n "$TZ" ]; then
	export TZ=$TZ
	echo "Using timezone: $TZ"
else
	echo "TZ variable is not set, using system timezone"
fi

# 1. Initialization of the database (if not initialized)
echo "Running aerich init-db..."
aerich init-db || true

# 2. Applying unapplied migrations
echo "Running aerich migrate..."
if ! aerich migrate; then
	echo "[ERROR] Aerich migrate failed. Please check migrations manually (there may be conflicting or unnecessary files)."
	exit 1
fi

# 2.1. Applying all migrations (upgrade)
echo "Running aerich upgrade..."
if ! aerich upgrade; then
	echo "[ERROR] Aerich upgrade failed. Please check migrations manually (there may be conflicting or unnecessary files)."
	exit 1
fi

# 3. Running main app in polling or webhook mode based on POLLING_MODE variable
if [ "$POLLING_MODE" = "True" ]; then
	echo "Running main.py in polling mode..."
	execpython main.py
else
	echo "Running main.py in webhook mode..."
	exec python main.py webhook
fi
