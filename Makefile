.PHONY: install dev dev-ui lint test run worker migrate tree

install:
	pip install -e ".[dev]"
	cd frontend && npm install

dev:
	PYTHONPATH=src CHAOS_AGENT_SIMULATE_EXECUTION=true python3 -m uvicorn chaos_agent.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000

dev-ui:
	cd frontend && npm run dev

worker:
	celery -A chaos_agent.workers.celery_app worker --loglevel=info

lint:
	ruff check src tests
	ruff format --check src tests

test:
	pytest tests/ -v

migrate:
	alembic -c src/chaos_agent/storage/migrations/alembic.ini upgrade head

tree:
	@find . -not -path '*/\.*' -not -path './Chaos*' | head -80
