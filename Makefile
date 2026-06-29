.PHONY: install install-hooks lint format check test test-cov pre-commit run docker-up docker-down clean setup reset-env

install:
	uv sync --all-extras

# One-time dev setup: sync deps, pin Python from .python-version, install git hooks.
setup: install install-hooks

# Recreate the virtualenv when scripts break after moving the repo (stale shebang paths).
reset-env:
	rm -rf .venv
	uv sync --all-extras

install-hooks:
	uv run pre-commit uninstall --hook-type commit-msg 2>/dev/null || true
	uv run pre-commit install --install-hooks
	uv run pre-commit install --hook-type pre-push --install-hooks

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
	uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker compose up -d postgres

docker-down:
	docker compose down

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
