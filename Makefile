.PHONY: install install-hooks lint format check test test-cov pre-commit run docker-up docker-down clean

install:
	uv sync --all-extras

install-hooks:
	uv run pre-commit install
	uv run pre-commit install --hook-type pre-push

lint:
	uv run ruff check app tests

format:
	uv run ruff format app tests
	uv run ruff check --fix app tests

check: lint
	uv run ruff format --check app tests
	uv run pytest -v

test:
	uv run pytest -v

test-cov:
	uv run pytest -v --cov=app --cov-report=term-missing

pre-commit:
	uv run pre-commit run --all-files

run:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker compose up -d postgres

docker-down:
	docker compose down

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
