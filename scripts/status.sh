#!/bin/bash
# Check service status

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVICE_NAME="scanner-proxy.service"

echo -e "${BLUE}Scanner Proxy Service Status:${NC}"
sudo systemctl status $SERVICE_NAME --no-pager || echo -e "${RED}Service not installed${NC}"

echo ""
echo -e "${BLUE}Docker Container Status:${NC}"
docker-compose ps 2>/dev/null || echo -e "${RED}Docker not running${NC}"
