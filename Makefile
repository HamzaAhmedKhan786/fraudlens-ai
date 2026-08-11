.PHONY: dev api web test lint infra-up infra-down

dev:
	docker compose up --build

api:
	cd apps/api && uvicorn fraudlens.main:app --reload

web:
	cd apps/web && npm run dev

test:
	cd apps/api && pytest

lint:
	cd apps/api && ruff check .
	cd apps/web && npm run lint

infra-up:
	docker compose up -d postgres redis kafka minio

infra-down:
	docker compose down

