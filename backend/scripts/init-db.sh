#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE nerd_analytics_db;
    GRANT ALL PRIVILEGES ON DATABASE nerd_analytics_db TO $POSTGRES_USER;
EOSQL
