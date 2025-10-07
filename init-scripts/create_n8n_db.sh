#!/bin/bash

set -e

export PGPASSWORD=$POSTGRES_PASSWORD

DB_EXISTS=$(psql -h postgresql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_database WHERE datname='n8n_db'")

if [ "$DB_EXISTS" = "1" ]; then
  echo "Database n8n_db already exists, skipping creation."
else
  psql -h postgresql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE DATABASE n8n_db;"
  psql -h postgresql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "GRANT ALL PRIVILEGES ON DATABASE n8n_db TO $POSTGRES_USER;"
fi
