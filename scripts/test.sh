#!/bin/bash
# Run tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

VENV_DIR="venv"

# Ensure setup is done first
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment not found, running setup first...${NC}"
    ./scripts/setup.sh
fi

echo -e "${BLUE}Running tests...${NC}"

$VENV_DIR/bin/python -c "import src.services.agent_discovery_response; print('✓ Agent service imports successfully')"
$VENV_DIR/bin/python -c "import src.services.file_transfer; print('✓ File transfer service imports successfully')"
$VENV_DIR/bin/python -c "import src.network.discovery; print('✓ Discovery service imports successfully')"

echo -e "${GREEN}✓ All tests passed!${NC}"
