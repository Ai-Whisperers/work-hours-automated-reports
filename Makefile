.PHONY: help install dev test lint format clean docker-build docker-run docker-stop report validate

# Variables
PYTHON := python
PIP := pip
DOCKER_IMAGE := clockify-ado-report
DOCKER_TAG := latest

# Default target
help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev          - Install development dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean cache and temporary files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run with Docker"
	@echo "  make docker-stop  - Stop Docker containers"
	@echo "  make report       - Generate report (local)"
	@echo "  make validate     - Validate configuration"

# Installation
install:
	$(PIP) install -r requirements.txt

dev: install
	$(PIP) install -r requirements-dev.txt || true
	pre-commit install || true

# Testing
test:
	pytest tests/ -v --cov=src --cov-report=html

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# Code quality
lint:
	ruff check src/
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/
	ruff check src/ --fix

# Cleaning
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	rm -rf reports/*.xlsx reports/*.html reports/*.pdf 2>/dev/null || true
	rm -rf .cache/* 2>/dev/null || true

clean-all: clean
	rm -rf venv/ .venv/

# Docker commands
docker-build:
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f app

docker-shell:
	docker-compose exec app /bin/bash

docker-clean:
	docker-compose down -v
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) || true

# Application commands
report:
	$(PYTHON) main.py run

report-week:
	$(PYTHON) main.py run --start $$(date -d '7 days ago' +%Y-%m-%d) --end $$(date +%Y-%m-%d)

report-month:
	$(PYTHON) main.py run --start $$(date -d '30 days ago' +%Y-%m-%d) --end $$(date +%Y-%m-%d)

validate:
	$(PYTHON) main.py validate

cache-clear:
	$(PYTHON) main.py cache clear

cache-stats:
	$(PYTHON) main.py cache stats

# Development helpers
shell:
	$(PYTHON)

run-dev:
	ENVIRONMENT=development $(PYTHON) main.py run --verbose

watch:
	watchmedo auto-restart --directory=./src --pattern="*.py" --recursive -- python main.py run

# Setup commands
setup: install dev
	cp .env.example .env
	@echo "Setup complete! Edit .env file with your API credentials"

setup-docker: docker-build
	cp .env.example .env
	@echo "Docker setup complete! Edit .env file with your API credentials"