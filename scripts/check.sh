#!/bin/bash
# Quick system check

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVICE_NAME="scanner-proxy.service"
VENV_DIR="venv"

echo -e "${BLUE}Quick System Check:${NC}"

echo -n "Docker: "
docker --version 2>/dev/null && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}"

echo -n "Docker Compose: "
docker-compose --version 2>/dev/null && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}"

echo -n "Python 3: "
python3 --version 2>/dev/null && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}"

echo -n "Virtual Environment: "
[ -d "$VENV_DIR" ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}Not created${NC}"

echo -n "Service Status: "
sudo systemctl is-active $SERVICE_NAME 2>/dev/null && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}Not running${NC}"
