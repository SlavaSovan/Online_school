CONTAINER_NAME = auth_service

.PHONY: help up down logs ps restart build create-admin shell logs-app logs-db clean

help:
	@echo "========================================="
	@echo "Available commands:"
	@echo "========================================="
	@echo ""
	@echo "Container management:"
	@echo "  make up          - Start all containers"
	@echo "  make up-dev      - Start all containers in dev mode"
	@echo "  make down        - Stop all containers"
	@echo "  make restart     - Restart all containers"
	@echo "  make ps          - Show container status"
	@echo "  make logs        - Show logs from all containers"
	@echo "  make logs-app    - Show logs only for app container"
	@echo ""
	@echo "App management:"
	@echo "  make build       - Rebuild app image"
	@echo "  make shell       - Open shell in app container"
	@echo "  make init		  - Create admin user (intaractive)"
	@echo "  make create-admin - Create admin user (intaractive)"
	@echo "  make db-shell    - Open psql in PostgreSQL container"
	@echo ""

up:
	@echo "Starting containers..."
	docker-compose up -d
	@echo "Done! Containers are running."
	@echo "  - App: http://localhost:8000/api/v1"
	@echo "  - PgAdmin: http://localhost:5050"

up-dev:
	@echo "Starting containers in dev mode..."
	docker-compose up --watch
	@echo "Done! Containers are running."
	@echo "  - App: http://localhost:8000/api/v1"
	@echo "  - PgAdmin: http://localhost:5050"

down:
	@echo "Stopping containers..."
	docker-compose down
	@echo "Containers stopped."

restart: down up
	@echo "Containers restarted."

ps:
	docker-compose ps

logs:
	docker-compose logs -f

logs-app:
	docker-compose logs -f app

logs-db:
	docker-compose logs -f postgres

build:
	@echo "Rebuilding app image..."
	docker-compose build app
	@echo "Image rebuilt."

shell:
	@echo "Opening shell in container $(CONTAINER_NAME)..."
	docker exec -it $(CONTAINER_NAME) bash

init:
	@echo "Starting admin creation..."
	@echo "Make sure container is running (make up)"
	@docker exec -it $(CONTAINER_NAME) python -m app.scripts.init_roles

create-admin:
	@echo "Starting admin creation..."
	@echo "Make sure container is running (make up)"
	@docker exec -it $(CONTAINER_NAME) python -m app.scripts.create_admin

db-shell:
	@echo "Connecting to PostgreSQL..."
	docker exec -it auth_postgres psql -U postgres -d auth_db