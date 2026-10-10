.DEFAULT_GOAL := help
.PHONY: help env up down logs ps test dev-api smoke load-test clean

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

env: ## Crée le fichier .env à partir de .env.example (s'il n'existe pas)
	@test -f .env || (cp .env.example .env && echo ".env créé : pense à changer le mot de passe")

up: env ## Construit et lance toute l'application (http://localhost:8080)
	docker compose up --build -d
	@echo "Application : http://localhost:8080   |   API : http://localhost:8000/docs"

down: ## Arrête les conteneurs (les données PostgreSQL sont conservées)
	docker compose down

logs: ## Suit les journaux de tous les services
	docker compose logs -f

ps: ## Affiche l'état des services
	docker compose ps

test: ## Lance les tests pytest de l'API dans un environnement virtuel
	cd app/api && python3 -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt && .venv/bin/python -m pytest -v

dev-api: ## Lance l'API seule, en local, avec SQLite (sans Docker)
	cd app/api && python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt && .venv/bin/uvicorn app.main:app --reload --port 8000

smoke: ## Lance le test de fumée contre l'application locale
	./scripts/smoke_test.sh http://localhost:8080

load-test: ## Lance un test de charge de 60 secondes contre l'application locale
	python3 scripts/load_test.py --url http://localhost:8080 --duration 60

clean: ## Supprime les conteneurs ET les données (volume PostgreSQL)
	docker compose down -v
