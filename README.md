# ScannerProxy - Network Scanner Agent Discovery & File Transfer Service

A Python-based network service that facilitates scanner discovery and secure file transfer operations over UDP/TCP protocols. The system can operate in both standalone mode (stores received files locally) and proxy mode (forwards files to target agents).

## Overview

ScannerProxy implements a network agent that:
- **Responds to scanner discovery broadcasts** on UDP port 706
- **Receives file transfer requests** and handles TCP file transfers on port 708  
- **Supports proxy mode** to forward received files to other network agents
- **Provides interactive testing tools** with rich CLI interfaces
- **Offers comprehensive deployment options** (local, Docker, system service)

## Prerequisites

- Python 3.12+ (recommended) or Python 3.8+
- Docker & Docker Compose (for containerized deployment)
- Linux system with systemd (for system service installation)
- Network access to UDP port 706 and TCP port 708

## Quick Commands

This project includes a comprehensive Makefile for easy development, testing, and deployment.

### 🚀 Development Setup
```bash
make setup          # Set up local Python environment & dependencies
make dev-setup      # Complete development setup with confirmation
make check          # Check system requirements and configuration
```

### 🧪 Testing & Development
```bash
make mock-scanner   # Run interactive mock scanner for testing
make service        # Run agent discovery service locally (standalone/proxy mode)
make test           # Run basic functionality tests  
make lint           # Check code syntax and style
```

### 🐳 Docker Operations
```bash
make docker-build   # Build Docker image for production
make docker-run     # Start containerized service with ipvlan network
make docker-stop    # Stop and remove container
make docker-logs    # View real-time container logs
```

### ⚙️ Production Deployment
```bash
make prod-deploy      # Complete production setup (build + install service)
make install-service  # Install as systemd service (auto-start on boot)
make status          # Check service status and health
make logs            # View service logs (filtered)
make remove-service  # Completely remove system service
```

### 🔧 Maintenance & Troubleshooting
```bash
make restart-service  # Restart system service
make emergency-stop   # Force stop all Scanner Proxy processes
make clean           # Clean up local development environment
```

## Typical Workflows

### Development & Testing Workflow
1. **Setup Environment**: `make setup` - Install dependencies and create virtual environment
2. **Test Scanner Communication**: `make mock-scanner` - Interactive testing with rich CLI
3. **Run Local Service**: `make service` - Test agent service locally
4. **Verify Functionality**: `make test` - Run automated tests

### Production Deployment Workflow  
1. **Complete Deployment**: `make prod-deploy` - Build Docker image and install system service
2. **Verify Service Health**: `make status` - Check systemd service status
3. **Monitor Operations**: `make logs` - View filtered service logs
4. **Update Configuration**: Edit `config/production.yml` and `make restart-service`

### Service Management
- **Health Check**: `make status` - Systemd service status, Docker container health  
- **Log Monitoring**: `make logs` - Filtered logs, or `make docker-logs` for container logs
- **Service Control**: `make restart-service` - Graceful service restart
- **Complete Removal**: `make remove-service` - Remove systemd service and cleanup

## Configuration

The service uses environment-specific YAML configuration files:

### Configuration Files
- **Development**: `config/development.yml` - Used for local testing (`make service`)
- **Production**: `config/production.yml` - Used in Docker containers and system service
- **Environment Control**: Set `SCANNER_CONFIG_ENV` environment variable

### Current Production Configuration
- **Operating Mode**: Proxy mode enabled
- **Proxy Target**: 192.168.1.138 (files are forwarded to this agent)  
- **Container IP**: 192.168.1.201 (ipvlan network configuration)
- **File Retention**: 10 files maximum (older files auto-deleted)
- **Network Ports**: UDP 706 (discovery), TCP 708 (file transfer)
- **Logging**: Production-level logging to `logs/scanner-prod.log`

### Key Configuration Options
```yaml
# Proxy mode configuration
proxy:
  enabled: true                    # Enable/disable proxy forwarding
  agent_ip_address: "192.168.1.138"  # Target agent for file forwarding

# Network settings  
network:
  udp_port: 706                   # Discovery and control messages
  tcp_port: 708                   # File data transfer
  discovery_timeout: 1.0          # Discovery response timeout

# File management
scanner:
  files_directory: "files"        # Directory for received files
  max_files_retention: 10         # Auto-cleanup old files
  default_src_name: "Scanner-Prod"  # Agent identification name
```

## Troubleshooting

### Service Issues
```bash
make status           # Check systemd service and Docker container status
make logs            # View filtered service logs for errors
make emergency-stop  # Force stop all Scanner Proxy processes
make restart-service # Restart system service with fresh state
```

### Development Issues
```bash
make clean          # Clean up virtual environment and cache files
make setup          # Recreate Python environment and dependencies
make lint           # Check for Python syntax errors
make test           # Run functionality tests
```

### Docker & Container Issues
```bash
make docker-stop    # Stop and remove container
make docker-build  # Rebuild image with latest changes
make docker-run     # Start fresh container instance
make docker-logs    # View detailed container logs
```

### Network Connectivity Issues
```bash
# Check port availability
sudo netstat -tulpn | grep -E ':(706|708)'

# Test UDP discovery port
sudo tcpdump -i any port 706

# Test TCP file transfer port  
sudo tcpdump -i any port 708

# Check Docker network configuration
docker network ls
docker network inspect scannerproxy_ipvlan-net
```

## Network Architecture

### Network Configuration
The service operates on a dual-protocol architecture:

- **UDP Port 706**: Discovery requests and control messages
  - Scanner broadcasts discovery messages
  - Agent responds with availability and capabilities
  - File transfer requests and acknowledgments

- **TCP Port 708**: File data transfer  
  - Reliable file data transmission
  - Progress tracking and error handling
  - Direct binary file transfer

### Container Networking
- **Network Type**: ipvlan (defined in docker-compose.yml)
- **Container IP**: 192.168.1.201 (static assignment)
- **Host Network Bridge**: Allows direct network access
- **Port Mapping**: 706/udp and 708/tcp exposed to host

## Project Architecture

### File Structure
```
ScannerProxy/
├── README.md                     # This quick start guide
├── TECHNICAL_DOCUMENTATION.md   # Detailed technical documentation  
├── README_DISCOVERY_RESPONSE.md # Agent discovery service documentation
├── Makefile                     # Build and deployment automation
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container image definition
├── docker-compose.yml           # Production container configuration
├── agent_discovery_app.py       # Main service application entry point
│
├── config/                      # Environment-specific configurations
│   ├── development.yml          # Local development settings
│   ├── production.yml           # Production/container settings  
│   └── proxy_test.yml           # Testing configuration
│
├── src/                         # Core application source code
│   ├── __init__.py
│   ├── __main__.py              # Module entry point
│   ├── agents/                  # Agent base classes and interfaces
│   ├── core/                    # Core business logic (ScannerService)
│   ├── dto/                     # Data transfer objects and models
│   ├── network/                 # Network protocols and discovery
│   ├── services/                # Service layer (discovery, file transfer)
│   └── utils/                   # Utilities (config, logging)
│
├── tests/                       # Test suite and mocks
│   └── mocks/                   
│       └── mock_scanner.py      # Interactive testing tool
│
├── scripts/                     # Automation and deployment scripts
│   ├── setup.sh                # Environment setup
│   ├── install-service.sh       # System service installation
│   ├── status.sh               # Service status checking
│   ├── logs.sh                 # Log viewing utilities
│   └── emergency-stop.sh       # Emergency process termination
│
├── logs/                       # Application logs
│   ├── scanner-dev.log         # Development logs
│   └── scanner-prod.log        # Production logs
│
└── files/                      # File storage and transfer
    ├── *.raw                   # Received scanner files
    └── *.jpg                   # Processed image files
```

### Key Components
- **AgentDiscoveryResponseService**: Handles discovery and file transfer requests
- **ScannerService**: Core orchestration and network operations  
- **FileTransferService**: Manages file upload/download over TCP
- **NetworkInterfaceManager**: Network interface detection and configuration
- **ScannerProtocolMessage**: Protocol message parsing and validation

For detailed technical information, see `TECHNICAL_DOCUMENTATION.md`

## Getting Help

```bash
make help           # Show all available commands
make --version      # Show Makefile version info
```

### Additional Documentation
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)**: Executive summary and comprehensive project overview
- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)**: Complete technical reference
- **[README_DISCOVERY_RESPONSE.md](README_DISCOVERY_RESPONSE.md)**: Agent discovery service details
- **Inline Documentation**: Comprehensive docstrings in all source modules
