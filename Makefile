.PHONY: help setup run migrate test cov lint format typecheck audit e2e demo check lock-check docker-build clean
PY := uv run python src/manage.py

help:
	@echo "Targets: setup run migrate test cov lint format typecheck audit e2e demo check lock-check docker-build"

setup:           ## install dependencies exactly as locked (requires uv.lock)
	uv sync --frozen
	uv run pre-commit install

run:
	$(PY) migrate --noinput
	$(PY) sync_roles
	$(PY) runserver

migrate:
	$(PY) migrate --noinput
	$(PY) sync_roles

test:
	uv run pytest

cov:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run djlint --lint src/templates

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy src

audit:
	uv run bandit -q -r src -c pyproject.toml
	uv export --frozen --no-dev --no-emit-project -o requirements.audit.txt
	uv run pip-audit -r requirements.audit.txt --no-deps --disable-pip

e2e:
	uv run playwright install chromium
	uv run pytest -m e2e --no-cov

demo:            ## local development only
	$(PY) load_demo_data

check:
	$(PY) check
	$(PY) makemigrations --check --dry-run

lock-check:
	uv lock --check

docker-build:
	docker build -t oderske-chasy:local .

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov requirements.audit.txt
