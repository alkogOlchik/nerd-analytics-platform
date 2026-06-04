#!/bin/bash
set -e

if [ "${SKIP_MIGRATIONS}" != "true" ]; then
    echo "Running database migrations..."
    cd /app/backend

    alembic upgrade head

    if [ -f analytics_alembic.ini ]; then
        alembic -c analytics_alembic.ini upgrade head
    fi

    cd /app
fi

echo "Starting server..."
exec "$@"
