#!/bin/sh

set -e

echo "Starting initialization..."

if [ ! -f /app/certs/jwt-private.pem ]; then
    echo "Generating JWT certificates..."
    mkdir -p /app/certs
    openssl genrsa -out /app/certs/jwt-private.pem 2048
    openssl rsa -in /app/certs/jwt-private.pem -pubout -out /app/certs/jwt-public.pem
    echo "Certificates generated"
fi

echo "Applying migrations..."
alembic upgrade head
echo "Migrations applied!"

echo "Initialization completed"
exec "$@"