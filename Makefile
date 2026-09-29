.PHONY: up down logs build ps shell migrate revision seed restart clean

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

shell:
	docker compose exec api bash

migrate:
	docker compose exec api alembic upgrade head

revision:
	docker compose exec api alembic revision --autogenerate -m "$(m)"

restart:
	docker compose restart api worker beat frontend

clean:
	docker compose down -v
	rm -rf data/postgres/* data/redis/*
