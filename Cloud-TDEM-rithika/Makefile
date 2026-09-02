.PHONY: help install setup run test lint format clean

help:
	@echo "TDEM Secure Vault - Development Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install     - Install dependencies"
	@echo "  make setup       - Setup development environment"
	@echo ""
	@echo "Running:"
	@echo "  make run         - Start FastAPI backend (auto-reload)"
	@echo "  make run-prod    - Start FastAPI backend (production)"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run test suite"
	@echo "  make test-verbose - Run tests with verbose output"
	@echo "  make coverage    - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint        - Run linting (pylint, flake8)"
	@echo "  make format      - Format code (black)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean       - Remove generated files"
	@echo "  make logs        - Show audit logs"
	@echo ""

install:
	pip install -r requirements.txt

setup: install
	@echo "Setting up TDEM development environment..."
	cp -n .env.example .env || true
	mkdir -p data/storage data/metadata data/metadata/audit
	@echo "✓ Setup complete!"
	@echo "Next: cp .env.example .env and update settings"

run:
	python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

run-prod:
	python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

test:
	python3 -m pytest tests/ -v

test-verbose:
	python3 -m pytest tests/ -vv -s

coverage:
	python3 -m pytest tests/ --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report generated: htmlcov/index.html"

lint:
	@echo "Running pylint..."
	python3 -m pylint app/ || true
	@echo "Running flake8..."
	python3 -m flake8 app/ --max-line-length=120 || true

format:
	@echo "Formatting code with black..."
	python3 -m black app/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"

logs:
	@echo "Recent audit logs:"
	tail -20 data/metadata/audit/audit_*.jsonl 2>/dev/null || echo "No audit logs yet"

# Quick development workflow
dev: setup
	@echo "Starting TDEM in development mode..."
	python3 -m uvicorn app.main:app --reload

# Run tests and show coverage
check: lint test coverage
