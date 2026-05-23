#!/usr/bin/env bash
# =============================================================================
# entrypoint.sh — стартовий скрипт для web-контейнера
#   - чекає, доки буде доступна БД
#   - запускає міграції та збирає статику
#   - передає управління команді CMD (gunicorn або celery)
# =============================================================================
set -euo pipefail

# ---- Wait for Postgres ------------------------------------------------------
if [[ "${WAIT_FOR_DB:-1}" == "1" ]]; then
    DB_HOST="${POSTGRES_HOST:-db}"
    DB_PORT="${POSTGRES_PORT:-5432}"
    echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
    for i in {1..60}; do
        if nc -z "${DB_HOST}" "${DB_PORT}"; then
            echo "[entrypoint] PostgreSQL is up."
            break
        fi
        sleep 1
    done
fi

# ---- Run Django startup tasks (тільки для web) ------------------------------
# Celery-контейнери НЕ повинні робити migrate/collectstatic.
if [[ "${RUN_MIGRATIONS:-0}" == "1" ]]; then
    echo "[entrypoint] Running migrations..."
    python manage.py migrate --noinput
fi

if [[ "${RUN_COLLECTSTATIC:-0}" == "1" ]]; then
    echo "[entrypoint] Collecting static files..."
    python manage.py collectstatic --noinput
fi

# ---- Hand off to CMD --------------------------------------------------------
echo "[entrypoint] Starting: $*"
exec "$@"
