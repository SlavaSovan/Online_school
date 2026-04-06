.PHONY: help up down logs ps restart build shell init create-admin db-shell clean

help:
	@echo "Available commands:"
	@echo ""
	@echo "Container management:"
	@echo "  make up            - Run all  containers"
	@echo "  make down          - Stop all containers"
	@echo "  make restart       - Restart all containers"
	@echo "  make ps            - Show container stastus"
	@echo "  make logs          - Show logs of all containers"
	@echo "  make logs-users    - Show logs of a users-service container"
	@echo "  make logs-courses  - Show logs of a courses-service container"
	@echo "  make logs-tasks    - Show logs of a tasks-service container"
	@echo "  make build         - Rebuild all containers"
	@echo "  make build-users   - Rebuild a users-service container"
	@echo "  make build-courses - Rebuild a courses-service container"
	@echo "  make build-tasks   - Rebuild a tasks-service container"
	@echo ""
	@echo "Services operations:"
	@echo "  make shell-users   - Open the shell in users-service container"
	@echo "  make shell-courses - Open the shell in courses-service container"
	@echo "  make shell-tasks   - Open the shell in tasks-service container"
	@echo "  make init-roles    - Initialize roles"
	@echo "  make create-admin  - Create admin"
	@echo ""
	@echo "Clean:"
	@echo "  make clean         - Stop and remove all containers"
	@echo "  make clean-full    - Full clean (containers, volumes, images)"
	@echo ""


up:
	@echo "Running all containers..."
	docker-compose up -d
	@echo "Done! Containers are running."
	@echo "  - Users Service: http://localhost/api/users/api/v1"
	@echo "  - Courses Service: http://localhost/api/courses/api/v1"
	@echo "  - Tasks Service: http://localhost/api/tasks/api/v1"
	@echo "  - PgAdmin: http://localhost:5050"
	@echo "  - Minio Console: http://localhost:9001"


down:
	@echo "Stopping all containers..."
	docker-compose down
	@echo "Containers have been stopped."


restart: down up
	@echo "Containers have been restarted."


ps:
	docker-compose ps


logs:
	docker-compose logs -f


logs-users:
	docker-compose logs -f users-service


logs-courses:
	docker-compose logs -f courses-service


logs-tasks:
	docker-compose logs -f tasks-service


build:
	@echo "Rebuilding all images..."
	docker-compose build
	@echo "Images have been rebuilt."


build-users:
	docker-compose build users-service


build-courses:
	docker-compose build courses-service


build-tasks:
	docker-compose build tasks-service


shell-users:
	docker exec -it users-service sh


shell-courses:
	docker exec -it courses-service sh


shell-tasks:
	docker exec -it tasks-service sh


init-roles:
	@echo "Roles initializing..."
	docker exec -it users-service python -m app.scripts.init_roles


create-admin:
	@echo "Starting admin creation..."
	@docker exec -it users-service python -m app.scripts.create_admin


clean:
	@echo "Stopping and removing containers..."
	docker-compose down
	@echo "Containers have been removed."


clean-full:
	@echo "Full cleaning..."
	docker-compose down -v --rmi all --remove-orphans
	@echo "All containers, volumes and images have been removed".