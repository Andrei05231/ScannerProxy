# Variables
IMAGE_NAME = scannerproxy
CONTAINER_NAME = scannerproxy
NETWORK_NAME = scannerproxy_ipvlan-net
PORT = 8000
TEST_IP_ADDRESS = 10.0.52.222
PYTHON = python3
PIP = pip3

# Default target
.DEFAULT_GOAL := help

# Help target
help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Environment Setup
setup: venv install-deps install-test-deps ## Complete development environment setup
	@echo "Development environment setup complete!"

venv: ## Create virtual environment
	$(PYTHON) -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

install-deps: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-test-deps: ## Install testing dependencies
	$(PIP) install pytest pytest-cov pytest-mock pytest-asyncio coverage pytest-watch

install-dev-deps: ## Install development dependencies (linting, formatting)
	$(PIP) install black isort flake8 mypy pre-commit

# Code Quality
format: ## Format code with black and isort
	black src/ tests/
	isort src/ tests/

lint: ## Run linting checks
	flake8 src/ tests/
	mypy src/

check: format lint ## Run all code quality checks

# Application Running
run: ## Run the main application
	$(PYTHON) run.py

run-dev: ## Run application in development mode
	SCANNER_ENV=development $(PYTHON) run.py

run-prod: ## Run application in production mode
	SCANNER_ENV=production $(PYTHON) run.py

# Testing
test: ## Run all tests
	$(PYTHON) -m pytest tests/ -v

test-unit: ## Run unit tests only
	$(PYTHON) -m pytest tests/unit/ -v

test-integration: ## Run integration tests only
	$(PYTHON) -m pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	$(PYTHON) -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v

test-coverage-xml: ## Run tests with XML coverage report (for CI)
	$(PYTHON) -m pytest tests/ --cov=src --cov-report=xml --cov-report=term-missing -v

test-watch: ## Run tests in watch mode
	ptw tests/ -- -v

# Specific test targets
test-config: ## Run configuration tests
	$(PYTHON) -m pytest tests/unit/test_config.py -v

test-scanner: ## Run scanner service tests
	$(PYTHON) -m pytest tests/unit/test_scanner_service.py -v

test-network: ## Run network-related tests
	$(PYTHON) -m pytest tests/unit/test_network_models.py tests/unit/test_discovery.py tests/unit/test_network_interfaces.py -v

test-protocols: ## Run message protocol tests
	$(PYTHON) -m pytest tests/unit/test_message_protocols.py -v

test-file-transfer: ## Run file transfer tests
	$(PYTHON) -m pytest tests/unit/test_file_transfer.py -v

# Docker Operations
build: ## Build the main Docker image
	docker build -t $(IMAGE_NAME):latest .

build-test: ## Build the Docker test image
	docker build -f Dockerfile.test -t $(IMAGE_NAME)-test1:latest .

build-all: build build-test ## Build all Docker images

# Docker Compose Operations
up: ## Start services with docker-compose
	docker-compose up -d

down: ## Stop services with docker-compose
	docker-compose down

restart: down up ## Restart services

logs: ## Show logs from docker-compose services
	docker-compose logs -f

# Docker Container Operations
run-container: ## Run the main Docker container
	docker run -it --rm --name $(CONTAINER_NAME) $(IMAGE_NAME):latest

run-test-container: ## Run the Docker test container
	docker run -it --rm --cap-add=NET_ADMIN --name $(CONTAINER_NAME)-test1 --network $(NETWORK_NAME) --ip $(TEST_IP_ADDRESS) $(IMAGE_NAME)-test1:latest

run-test-debug: ## Run test container in debug mode
	docker run -it --rm --cap-add=NET_ADMIN --entrypoint /bin/bash --name $(CONTAINER_NAME)-test1 --network $(NETWORK_NAME) --ip $(TEST_IP_ADDRESS) $(IMAGE_NAME)-test1:latest

# Local Development Servers
local-server: ## Run local server for development
	CONT_IP=127.0.0.1 DEV_NAME=Custom-Scn1 DESTINATION=scan1 $(PYTHON) src/main.py

local-client: ## Run local client for testing
	CONT_IP=127.0.0.1 DEV_NAME=Custom-Scn1-test DESTINATION=scan1 $(PYTHON) src/receiver_proxy.py

# Cleaning and Maintenance
clean: clean-test clean-build clean-docker ## Clean all artifacts

clean-test: ## Clean test artifacts
	-rm -rf .pytest_cache/
	-rm -rf htmlcov/
	-rm -f coverage.xml
	-rm -f .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-build: ## Clean build artifacts
	-rm -rf build/
	-rm -rf dist/
	-rm -rf *.egg-info/
	-rm -rf .tox/
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

clean-docker: ## Clean Docker images and containers
	docker system prune -f
	-docker rmi $(IMAGE_NAME):latest $(IMAGE_NAME)-test1:latest 2>/dev/null || true

clean-logs: ## Clean log files
	-rm -rf logs/*.log
	-find logs/ -name "*.log" -delete 2>/dev/null || true

# Security and Dependency Management
security-check: ## Run security checks on dependencies
	pip-audit --desc --format=json --output security-report.json || true
	pip-audit --desc

update-deps: ## Update dependencies (run with caution)
	pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U

freeze-deps: ## Freeze current dependencies to requirements.txt
	pip freeze > requirements-frozen.txt

# Documentation
docs: ## Generate documentation
	@echo "Generating project documentation..."
	@echo "# ScannerProxy Documentation" > docs/API.md
	@echo "" >> docs/API.md
	@echo "## Module Documentation" >> docs/API.md
	@find src -name "*.py" -exec echo "### {}" \; -exec head -20 {} \; >> docs/API.md
	@echo "Documentation generated in docs/"

docs-coverage: ## Generate test coverage documentation
	@echo "Generating coverage documentation..."
	@mkdir -p docs
	@$(PYTHON) -m pytest tests/ --cov=src --cov-report=html --cov-report=term > docs/coverage-report.txt 2>&1
	@echo "Coverage documentation generated in htmlcov/ and docs/coverage-report.txt"

docs-clean: ## Clean documentation artifacts
	-rm -rf docs/
	-rm -rf htmlcov/

# CI/CD Support
ci-test: install-test-deps test-coverage-xml ## Run tests for CI/CD pipeline
	@echo "CI tests completed"

pre-commit: check test ## Run pre-commit checks
	@echo "Pre-commit checks passed"

# Development Utilities
show-config: ## Show current configuration
	@echo "Environment: $${SCANNER_ENV:-development}"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "Current directory: $(shell pwd)"

show-structure: ## Show project structure
	tree -I 'venv|__pycache__|*.pyc|.git|.pytest_cache|htmlcov' -L 3

# Network Setup (for Docker networking)
create-network: ## Create Docker network for testing
	docker network create --driver=ipvlan --subnet=10.0.52.0/24 --gateway=10.0.52.1 -o parent=eth0 $(NETWORK_NAME) || true

remove-network: ## Remove Docker network
	docker network rm $(NETWORK_NAME) || true

.PHONY: help setup venv install-deps install-test-deps install-dev-deps format lint check run run-dev run-prod test test-unit test-integration test-coverage test-coverage-xml test-watch test-config test-scanner test-network test-protocols test-file-transfer build build-test build-all up down restart logs run-container run-test-container run-test-debug local-server local-client clean clean-test clean-build clean-docker clean-logs security-check update-deps freeze-deps docs docs-coverage docs-clean ci-test pre-commit show-config show-structure create-network remove-network