#!/bin/bash
# Install Scanner Proxy as system service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVICE_NAME="scanner-proxy.service"
WORKING_DIR=$(pwd)

echo -e "${BLUE}Installing Scanner Proxy as system service...${NC}"

# Build Docker image first
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t scanner-proxy:latest .

# Create systemd service file
if [ ! -f "/etc/systemd/system/$SERVICE_NAME" ]; then
    echo -e "${YELLOW}Creating systemd service file...${NC}"
    sudo tee /etc/systemd/system/$SERVICE_NAME > /dev/null << EOF
[Unit]
Description=Scanner Proxy Agent Service
Requires=docker.service
After=docker.service

[Service]
Type=forking
RemainAfterExit=yes
WorkingDirectory=$WORKING_DIR
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
fi

echo -e "${YELLOW}Reloading systemd and enabling service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo -e "${GREEN}✓ Scanner Proxy Agent Service installed and started!${NC}"
echo -e "${BLUE}Service will now start automatically at boot${NC}"
echo -e "${YELLOW}Use 'make status' to check service status${NC}"
