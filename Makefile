# Development (no Docker): backend + frontend with hot reload. Stop with Ctrl+C.
dev:
	./start-dev.sh

# Development with Docker: same but in containers. First time use --build.
dev-docker:
	docker compose -f docker-compose.dev.yml up

dev-docker-build:
	docker compose -f docker-compose.dev.yml up --build

.PHONY: dev dev-docker dev-docker-build
