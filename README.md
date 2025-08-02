# Scanner Proxy - Quick Start Guide

This project includes a comprehensive Makefile for easy development, testing, and deployment.

## Prerequisites

- Python 3.8+
- Docker & Docker Compose
- Linux system with systemd (for service installation)

## Quick Commands

### 🚀 Development Setup
```bash
make setup          # Set up local Python environment
make dev-setup      # Complete development setup
make check          # Check system requirements
```

### 🧪 Testing & Development
```bash
make mock-scanner   # Run interactive mock scanner
make service        # Run agent discovery service locally
make test           # Run basic tests
make lint           # Check code syntax
```

### 🐳 Docker Operations
```bash
make docker-build   # Build Docker image
make docker-run     # Start containerized service
make docker-stop    # Stop container
make docker-logs    # View container logs
```

### ⚙️ Production Deployment
```bash
make install-service  # Install as system service (auto-start)
make status          # Check service status
make logs            # View service logs
make remove-service  # Remove system service
```

### 🔧 Maintenance
```bash
make restart-service  # Restart system service
make emergency-stop   # Stop all Scanner Proxy processes
make clean           # Clean up local environment
```

## Typical Workflows

### Development Workflow
1. `make setup` - Set up environment
2. `make mock-scanner` - Test scanner functionality
3. `make service` - Test service locally

### Production Deployment
1. `make prod-deploy` - Complete production setup
2. `make status` - Verify service is running
3. `make logs` - Monitor service logs

### Service Management
- `make status` - Check if service is running
- `make restart-service` - Restart the service
- `make remove-service` - Completely remove service

## Configuration

The service uses configuration from:
- **Development**: `config/development.yml`
- **Production**: `config/production.yml` (used in Docker)

Current production configuration:
- **Proxy Mode**: Enabled
- **Target Agent**: 192.168.1.138
- **Container IP**: 192.168.1.201
- **File Retention**: 10 files maximum

## Troubleshooting

### Service Won't Start
```bash
make status          # Check service status
make logs           # Check error logs
make emergency-stop # Stop all processes
make restart-service # Try restarting
```

### Docker Issues
```bash
make docker-stop    # Stop container
make docker-build  # Rebuild image
make docker-run    # Start fresh container
```

### Development Issues
```bash
make clean         # Clean environment
make setup         # Recreate environment
make test          # Verify functionality
```

## Network Configuration

The service operates on:
- **UDP Port 706**: Discovery requests
- **TCP Port 708**: File transfers
- **Container IP**: 192.168.1.201 (ipvlan network)

## File Structure

```
Scanner Proxy/
├── Makefile              # Build and deployment commands
├── docker-compose.yml    # Container configuration
├── Dockerfile           # Container image definition
├── agent_discovery_app.py # Main service application
├── config/              # Configuration files
├── src/                 # Source code
├── tests/mocks/         # Test utilities
└── logs/               # Service logs
```

For detailed help: `make help`
