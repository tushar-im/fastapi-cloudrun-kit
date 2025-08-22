.PHONY: dev firebase-emulator seed-data test lint format typecheck test-cov pre-commit-install help clean

# Default target
help:
	@echo "Available commands:"
	@echo "  dev              - Run development server"
	@echo "  firebase-emulator - Start Firebase emulator"
	@echo "  seed-data        - Seed database with test data"
	@echo "  test             - Run tests"
	@echo "  lint             - Run linting checks"
	@echo "  format           - Format code"
	@echo "  typecheck        - Run type checking"
	@echo "  test-cov         - Run tests with coverage"
	@echo "  pre-commit-install - Install pre-commit hooks"
	@echo "  clean            - Clean up generated files"

dev:
	uv run python scripts/dev.py

firebase-emulator:
	uv run python scripts/firebase.py

seed-data:
	uv run python scripts/seed.py

test:
	uv run python scripts/test.py

lint:
	uv run ruff check app tests

format:
	uv run ruff format app tests

typecheck:
	uv run mypy app

test-cov:
	uv run pytest --cov=app --cov-report=html --cov-report=term-missing

pre-commit-install:
	uv run pre-commit install

# Additional useful targets
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/

# Run all checks (useful for CI)
check: lint typecheck test

# Install dependencies and set up the project
setup:
	uv sync
	$(MAKE) pre-commit-install