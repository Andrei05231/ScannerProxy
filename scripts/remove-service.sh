#!/bin/bash
# Remove Scanner Proxy system service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVICE_NAME="scanner-proxy.service"

echo -e "${YELLOW}Removing Scanner Proxy system service...${NC}"

sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
sudo systemctl disable $SERVICE_NAME 2>/dev/null || true
sudo rm -f /etc/systemd/system/$SERVICE_NAME
sudo systemctl daemon-reload

echo -e "${GREEN}✓ Scanner Proxy service removed!${NC}"
