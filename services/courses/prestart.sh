#!/bin/sh

set -e

echo "Run apply migrations..."
python manage.py migrate
echo "Migrations applied!"

exec "$@"