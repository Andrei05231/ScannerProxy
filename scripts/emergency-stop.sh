#!/bin/bash
# Emergency stop all Scanner Proxy processes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVICE_NAME="scanner-proxy.service"

echo -e "${RED}Emergency stop - stopping all Scanner Proxy processes...${NC}"

sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
docker-compose -p scanner-proxy down 2>/dev/null || true
pkill -f "agent_discovery_app.py" 2>/dev/null || true

echo -e "${GREEN}✓ All processes stopped${NC}"
