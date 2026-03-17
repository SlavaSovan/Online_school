#!/bin/sh

set -e

echo "Run apply migrations..."

echo "Waiting for postgres..."

while ! pg_isready -h $DB_HOST -p $DB_PORT
do
  sleep 1
done

echo "Postgres ready"

python manage.py migrate

echo "Migrations applied!"

exec "$@"