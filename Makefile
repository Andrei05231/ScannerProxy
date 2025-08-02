# Scanner Proxy Makefile
# Provides easy commands for development, testing, and deployment

# Configuration
SCRIPTS_DIR := scripts
VENV_DIR := venv

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help setup clean mock-scanner service docker-build docker-run docker-stop install-service remove-service status logs test lint check emergency-stop restart-service

# Default target
help:
	@echo "$(BLUE)Scanner Proxy - Available Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Development & Testing:$(NC)"
	@echo "  make setup          - Set up local Python environment"
	@echo "  make mock-scanner   - Run the mock scanner for testing"
	@echo "  make service        - Run the agent service locally (standalone/proxy mode)"
	@echo "  make clean          - Clean up local environment"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run code linting"
	@echo ""
	@echo "$(YELLOW)Docker Operations:$(NC)"
	@echo "  make docker-build   - Build the Docker image"
	@echo "  make docker-run     - Run service in Docker container"
	@echo "  make docker-stop    - Stop Docker container"
	@echo "  make docker-logs    - View Docker container logs"
	@echo ""
	@echo "$(YELLOW)System Service:$(NC)"
	@echo "  make install-service - Install as system service (auto-start)"
	@echo "  make remove-service  - Remove system service"
	@echo "  make status         - Check service status"
	@echo "  make logs           - View service logs"
	@echo "  make restart-service - Restart system service"
	@echo ""
	@echo "$(YELLOW)Utility:$(NC)"
	@echo "  make check          - Quick system check"
	@echo "  make emergency-stop - Stop all processes"

# Local Environment
setup:
	@$(SCRIPTS_DIR)/setup.sh

clean:
	@$(SCRIPTS_DIR)/clean.sh

# Development & Testing
mock-scanner: setup
	@echo "$(BLUE)Starting Mock Scanner...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@$(VENV_DIR)/bin/python -m tests.mocks.mock_scanner

service: setup
	@echo "$(BLUE)Starting Agent Service...$(NC)"
	@echo "$(YELLOW)Mode: Standalone (stores files) or Proxy (forwards files)$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@$(VENV_DIR)/bin/python agent_discovery_app.py

test:
	@$(SCRIPTS_DIR)/test.sh

lint: setup
	@echo "$(BLUE)Running code linting...$(NC)"
	@$(VENV_DIR)/bin/python -m py_compile src/services/*.py
	@$(VENV_DIR)/bin/python -m py_compile src/network/*.py
	@$(VENV_DIR)/bin/python -m py_compile src/utils/*.py
	@$(VENV_DIR)/bin/python -m py_compile agent_discovery_app.py
	@echo "$(GREEN)✓ No syntax errors found!$(NC)"

# Docker Operations
docker-build:
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker build -t scanner-proxy:latest .
	@echo "$(GREEN)✓ Docker image built successfully!$(NC)"

docker-run: docker-build
	@echo "$(BLUE)Starting Docker container...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Docker container started!$(NC)"
	@echo "$(YELLOW)Use 'make docker-logs' to view logs$(NC)"
	@echo "$(YELLOW)Use 'make docker-stop' to stop the container$(NC)"

docker-stop:
	@echo "$(YELLOW)Stopping Docker container...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Docker container stopped!$(NC)"

docker-logs:
	@echo "$(BLUE)Docker container logs:$(NC)"
	@docker-compose logs -f

# System Service Management
install-service:
	@$(SCRIPTS_DIR)/install-service.sh

remove-service:
	@$(SCRIPTS_DIR)/remove-service.sh

status:
	@$(SCRIPTS_DIR)/status.sh

logs:
	@$(SCRIPTS_DIR)/logs.sh

restart-service:
	@echo "$(YELLOW)Restarting Scanner Proxy service...$(NC)"
	@sudo systemctl restart scanner-proxy.service
	@echo "$(GREEN)✓ Service restarted$(NC)"

# Utility Commands
check:
	@$(SCRIPTS_DIR)/check.sh

emergency-stop:
	@$(SCRIPTS_DIR)/emergency-stop.sh

# Development shortcuts
dev-setup: setup
	@echo "$(BLUE)Development environment ready!$(NC)"
	@echo "$(YELLOW)Available commands:$(NC)"
	@echo "  make mock-scanner  - Test with mock scanner"
	@echo "  make service       - Run agent service locally"
	@echo "  make test          - Run tests"

prod-deploy: docker-build install-service
	@echo "$(GREEN)✓ Production deployment complete!$(NC)"
	@echo "$(BLUE)Scanner Proxy Agent Service is now running as a system service$(NC)"
