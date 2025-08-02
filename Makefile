# Scanner Proxy Makefile
# Provides easy commands for development, testing, and deployment

# Configuration
PYTHON := python3
VENV_DIR := venv
SERVICE_NAME := scanner-proxy
DOCKER_IMAGE := scanner-proxy:latest
CONTAINER_NAME := scanner-proxy-prod
SYSTEMD_SERVICE := scanner-proxy.service

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help setup clean mock-scanner service docker-build docker-run docker-stop install-service remove-service status logs

# Default target
help:
	@echo "$(BLUE)Scanner Proxy - Available Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Development & Testing:$(NC)"
	@echo "  make setup          - Set up local Python environment"
	@echo "  make mock-scanner   - Run the mock scanner for testing"
	@echo "  make service        - Run the agent discovery service locally"
	@echo "  make clean          - Clean up local environment"
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
	@echo ""
	@echo "$(YELLOW)Utility:$(NC)"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run code linting"

# Local Environment Setup
setup:
	@echo "$(BLUE)Setting up local Python environment...$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	@$(VENV_DIR)/bin/pip install --upgrade pip
	@$(VENV_DIR)/bin/pip install -r requirements.txt
	@echo "$(GREEN)✓ Local environment setup complete!$(NC)"
	@echo "$(BLUE)To activate: source $(VENV_DIR)/bin/activate$(NC)"

clean:
	@echo "$(YELLOW)Cleaning up local environment...$(NC)"
	@rm -rf $(VENV_DIR)
	@rm -rf src/__pycache__
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

# Development & Testing
mock-scanner: setup
	@echo "$(BLUE)Starting Mock Scanner...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@cd . && $(VENV_DIR)/bin/python tests/mocks/mock_scanner.py

service: setup
	@echo "$(BLUE)Starting Agent Discovery Service...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@cd . && $(VENV_DIR)/bin/python agent_discovery_app.py

test: setup
	@echo "$(BLUE)Running tests...$(NC)"
	@$(VENV_DIR)/bin/python -c "import src.services.agent_discovery_response; print('✓ Agent discovery response service imports successfully')"
	@$(VENV_DIR)/bin/python -c "import src.services.file_transfer; print('✓ File transfer service imports successfully')"
	@$(VENV_DIR)/bin/python -c "import src.network.discovery; print('✓ Discovery service imports successfully')"
	@echo "$(GREEN)✓ All tests passed!$(NC)"

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
	@docker build -t $(DOCKER_IMAGE) .
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
install-service: docker-build
	@echo "$(BLUE)Installing Scanner Proxy as system service...$(NC)"
	@if [ ! -f "/etc/systemd/system/$(SYSTEMD_SERVICE)" ]; then \
		echo "$(YELLOW)Creating systemd service file...$(NC)"; \
		sudo tee /etc/systemd/system/$(SYSTEMD_SERVICE) > /dev/null << 'EOF'; \
[Unit]; \
Description=Scanner Proxy Service; \
Requires=docker.service; \
After=docker.service; \
; \
[Service]; \
Type=forking; \
RemainAfterExit=yes; \
WorkingDirectory=$(shell pwd); \
ExecStart=/usr/bin/docker-compose up -d; \
ExecStop=/usr/bin/docker-compose down; \
TimeoutStartSec=0; \
; \
[Install]; \
WantedBy=multi-user.target; \
EOF \
	fi
	@echo "$(YELLOW)Reloading systemd and enabling service...$(NC)"
	@sudo systemctl daemon-reload
	@sudo systemctl enable $(SYSTEMD_SERVICE)
	@sudo systemctl start $(SYSTEMD_SERVICE)
	@echo "$(GREEN)✓ Scanner Proxy service installed and started!$(NC)"
	@echo "$(BLUE)Service will now start automatically at boot$(NC)"
	@echo "$(YELLOW)Use 'make status' to check service status$(NC)"

remove-service:
	@echo "$(YELLOW)Removing Scanner Proxy system service...$(NC)"
	@sudo systemctl stop $(SYSTEMD_SERVICE) 2>/dev/null || true
	@sudo systemctl disable $(SYSTEMD_SERVICE) 2>/dev/null || true
	@sudo rm -f /etc/systemd/system/$(SYSTEMD_SERVICE)
	@sudo systemctl daemon-reload
	@echo "$(GREEN)✓ Scanner Proxy service removed!$(NC)"

status:
	@echo "$(BLUE)Scanner Proxy Service Status:$(NC)"
	@sudo systemctl status $(SYSTEMD_SERVICE) --no-pager || echo "$(RED)Service not installed$(NC)"
	@echo ""
	@echo "$(BLUE)Docker Container Status:$(NC)"
	@docker-compose ps 2>/dev/null || echo "$(RED)Docker not running$(NC)"

logs:
	@echo "$(BLUE)Scanner Proxy Service Logs:$(NC)"
	@sudo journalctl -u $(SYSTEMD_SERVICE) --no-pager -n 50

# Development shortcuts
dev-setup: setup
	@echo "$(BLUE)Development environment ready!$(NC)"
	@echo "$(YELLOW)Available commands:$(NC)"
	@echo "  make mock-scanner  - Test with mock scanner"
	@echo "  make service       - Run service locally"
	@echo "  make test          - Run tests"

prod-deploy: docker-build install-service
	@echo "$(GREEN)✓ Production deployment complete!$(NC)"
	@echo "$(BLUE)Scanner Proxy is now running as a system service$(NC)"

# Quick status check
check:
	@echo "$(BLUE)Quick System Check:$(NC)"
	@echo -n "Docker: "
	@docker --version 2>/dev/null && echo "$(GREEN)✓$(NC)" || echo "$(RED)✗$(NC)"
	@echo -n "Docker Compose: "
	@docker-compose --version 2>/dev/null && echo "$(GREEN)✓$(NC)" || echo "$(RED)✗$(NC)"
	@echo -n "Python 3: "
	@$(PYTHON) --version 2>/dev/null && echo "$(GREEN)✓$(NC)" || echo "$(RED)✗$(NC)"
	@echo -n "Virtual Environment: "
	@[ -d "$(VENV_DIR)" ] && echo "$(GREEN)✓$(NC)" || echo "$(YELLOW)Not created$(NC)"
	@echo -n "Service Status: "
	@sudo systemctl is-active $(SYSTEMD_SERVICE) 2>/dev/null && echo "$(GREEN)✓$(NC)" || echo "$(YELLOW)Not running$(NC)"

# Emergency commands
emergency-stop:
	@echo "$(RED)Emergency stop - stopping all Scanner Proxy processes...$(NC)"
	@sudo systemctl stop $(SYSTEMD_SERVICE) 2>/dev/null || true
	@docker-compose down 2>/dev/null || true
	@pkill -f "agent_discovery_app.py" 2>/dev/null || true
	@echo "$(GREEN)✓ All processes stopped$(NC)"

restart-service:
	@echo "$(YELLOW)Restarting Scanner Proxy service...$(NC)"
	@sudo systemctl restart $(SYSTEMD_SERVICE)
	@echo "$(GREEN)✓ Service restarted$(NC)"
