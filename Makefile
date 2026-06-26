.PHONY: install dev dev-ui lint test run worker migrate tree lock

install:
	uv sync --extra dev
	cd frontend && npm install

lock:
	uv lock

dev:
	CHAOS_AGENT_SIMULATE_EXECUTION=true uv run uvicorn chaos_agent.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000

dev-ui:
	cd frontend && npm run dev

worker:
	uv run celery -A chaos_agent.workers.celery_app worker --loglevel=info

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

test:
	uv run pytest tests/ -v

migrate:
	uv run alembic -c src/chaos_agent/storage/migrations/alembic.ini upgrade head

tree:
	@find . -not -path '*/\.*' -not -path './Chaos*' | head -80
