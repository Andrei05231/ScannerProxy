#!/bin/bash

# Scanner Proxy Production Deployment Script

set -e

echo "🚀 Starting Scanner Proxy Production Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if docker and docker-compose are installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs files

# Set proper permissions
print_status "Setting permissions..."
chmod 755 logs files

# Stop existing container if running
print_status "Stopping existing container if running..."
docker-compose down || true

# Build the container
print_status "Building Scanner Proxy container..."
docker-compose build

# Start the service
print_status "Starting Scanner Proxy service..."
docker-compose up -d

# Wait a moment for startup
sleep 5

# Check service status
print_status "Checking service status..."
if docker-compose ps | grep -q "Up"; then
    print_success "Scanner Proxy is running successfully!"
    
    # Show configuration
    echo
    print_status "Current Configuration:"
    echo "  - Environment: production"
    echo "  - UDP Port: 706"
    echo "  - TCP Port: 708"
    echo "  - Proxy Mode: $(grep 'enabled:' config/production.yml | awk '{print $2}')"
    echo "  - Target Agent: $(grep 'agent_ip_address:' config/production.yml | awk '{print $2}' | tr -d '\"')"
    echo "  - Max File Retention: $(grep 'max_files_retention:' config/production.yml | awk '{print $2}')"
    
    echo
    print_status "Useful commands:"
    echo "  View logs:     docker-compose logs -f"
    echo "  Stop service:  docker-compose down"
    echo "  Restart:       docker-compose restart"
    echo "  Check status:  docker-compose ps"
    
else
    print_error "Failed to start Scanner Proxy service"
    print_status "Checking logs..."
    docker-compose logs
    exit 1
fi
