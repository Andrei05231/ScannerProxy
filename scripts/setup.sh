#!/bin/bash
# Setup local Python environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

VENV_DIR="venv"
PYTHON="python3"

echo -e "${BLUE}Setting up local Python environment...${NC}"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON -m venv $VENV_DIR
fi

echo -e "${YELLOW}Installing dependencies...${NC}"
$VENV_DIR/bin/pip install --upgrade pip
$VENV_DIR/bin/pip install -r requirements.txt

echo -e "${GREEN}✓ Local environment setup complete!${NC}"
echo -e "${BLUE}To activate: source $VENV_DIR/bin/activate${NC}"
