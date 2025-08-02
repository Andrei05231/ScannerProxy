#!/bin/bash
# View service logs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVICE_NAME="scanner-proxy.service"

echo -e "${BLUE}Scanner Proxy Service Logs:${NC}"
sudo journalctl -u $SERVICE_NAME --no-pager -n 50
