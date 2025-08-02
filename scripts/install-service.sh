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

# Check if Docker is available and get its path
DOCKER_PATH=$(which docker 2>/dev/null || echo "")
if [ -z "$DOCKER_PATH" ]; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

echo -e "${YELLOW}Found Docker at: $DOCKER_PATH${NC}"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker daemon is not running${NC}"
    exit 1
fi

# Build Docker image first
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t scanner-proxy:latest .

# Create systemd service file
if [ ! -f "/etc/systemd/system/$SERVICE_NAME" ]; then
    echo -e "${YELLOW}Creating systemd service file...${NC}"
    
    # Check if docker.service exists in systemd
    echo -e "${YELLOW}Checking if Docker is managed by systemd...${NC}"
    if systemctl list-unit-files | grep -q "docker.service"; then
        # Docker is managed by systemd
        echo -e "${YELLOW}Docker is managed by systemd, creating service with Docker dependency...${NC}"
        sudo tee /etc/systemd/system/$SERVICE_NAME > /dev/null << EOF
[Unit]
Description=Scanner Proxy Agent Service
Requires=docker.service
After=docker.service

[Service]
Type=forking
RemainAfterExit=yes
WorkingDirectory=$WORKING_DIR
ExecStart=$DOCKER_PATH compose up -d
ExecStop=$DOCKER_PATH compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    else
        # Docker is not managed by systemd (e.g., Docker Desktop)
        echo -e "${YELLOW}Docker is not managed by systemd, creating service without Docker dependency...${NC}"
        sudo tee /etc/systemd/system/$SERVICE_NAME > /dev/null << EOF
[Unit]
Description=Scanner Proxy Agent Service
After=network.target

[Service]
Type=forking
RemainAfterExit=yes
WorkingDirectory=$WORKING_DIR
ExecStart=$DOCKER_PATH compose up -d
ExecStop=$DOCKER_PATH compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    fi
fi

echo -e "${YELLOW}Reloading systemd and enabling service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo -e "${GREEN}✓ Scanner Proxy Agent Service installed and started!${NC}"
echo -e "${BLUE}Service will now start automatically at boot${NC}"
echo -e "${YELLOW}Use 'make status' to check service status${NC}"
