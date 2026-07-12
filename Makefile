# Python version is pinned via `.python-version` (used by uv and CI).
PYTHON_VERSION := $(shell tr -d '[:space:]' < .python-version)

UV = uv run

.PHONY: all clean dead-code format help install lint test

help: ## Show this help message
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

install: ## Install dependencies
	@echo "Installing dependencies..."
	uv python install $(PYTHON_VERSION)
	uv sync --python $(PYTHON_VERSION)
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install

format: ## Format code
	@echo "Formatting code..."
	$(UV) black . && $(UV) isort .

lint: ## Run linting tools
	@echo "Running linting tools..."
	$(UV) black --check . && \
	$(UV) isort --check-only . && \
	$(UV) flake8 . && \
	$(UV) mypy && \
	$(UV) bandit -c pyproject.toml -r src/

audit: ## Check dependencies for known vulnerabilities
	@echo "Auditing dependencies..."
	uv run pip-audit

dead-code: ## Check for dead code using vulture
	@echo "Checking for dead code..."
	uv run vulture

test: ## Run tests with coverage
	@echo "Running tests with coverage..."
	$(UV) python -m pytest -v --cov --cov-report=term-missing --cov-report=html

all: lint test dead-code ## Run lint, test, and dead-code check
	@echo "All checks completed successfully!"

clean: ## Clean cache and temporary files
	@echo "Cleaning cache and temporary files..."
	rm -rf .mypy_cache/ .pytest_cache/ .venv/ build/ dist/ htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
