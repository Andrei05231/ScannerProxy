#!/bin/bash
# Clean up local environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

VENV_DIR="venv"

echo -e "${YELLOW}Cleaning up local environment...${NC}"

rm -rf $VENV_DIR
rm -rf src/__pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo -e "${GREEN}✓ Cleanup complete!${NC}"
