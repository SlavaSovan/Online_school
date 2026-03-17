#!/bin/sh

set -e

echo "Run apply migrations..."

echo "Waiting for postgres..."

while ! pg_isready -h $DATABASE__DB_HOST -p $DATABASE__DB_PORT
do
  sleep 1
done

echo "Postgres ready"

alembic upgrade head

echo "Migrations applied!"

exec "$@"
