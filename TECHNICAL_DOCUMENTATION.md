# ScannerProxy Technical Documentation

## Project Overview

ScannerProxy is a Python-based network service that facilitates secure scanner discovery and file transfer operations over UDP/TCP protocols. The system implements a modular, SOLID-principled architecture supporting both standalone mode (local file storage) and proxy mode (file forwarding to target agents). Built with modern Python practices, it provides comprehensive deployment options including local development, Docker containerization, and systemd service integration.

### Key Features
- **Dual-Mode Operation**: Standalone file storage or proxy forwarding
- **Protocol Implementation**: Custom UDP/TCP scanner communication protocol
- **Rich Testing Tools**: Interactive CLI with progress tracking and network visualization
- **Production Ready**: Docker containers, systemd services, health monitoring
- **Comprehensive Logging**: Structured logging with rotation and filtering
- **Network Discovery**: Automatic interface detection and agent discovery
- **File Management**: Automatic retention policies and cleanup

### Target Use Cases
- Scanner network integration and file routing
- Legacy scanner modernization with proxy capabilities  
- Network testing and protocol development
- Document workflow automation and processing

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Requirements](#system-requirements)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [Core Components](#core-components)
6. [Network Protocol](#network-protocol)
7. [File Structure](#file-structure)
8. [API Documentation](#api-documentation)
9. [Usage Examples](#usage-examples)
10. [Testing](#testing)
11. [Deployment](#deployment)
12. [Proxy Mode](#proxy-mode)
13. [Troubleshooting](#troubleshooting)
14. [Maintenance](#maintenance)
15. [Security Considerations](#security-considerations)
16. [Extension Points](#extension-points)

## Architecture Overview

### Design Principles

The ScannerProxy follows SOLID design principles:

- **Single Responsibility Principle (SRP)**: Each class has one reason to change
- **Open-Closed Principle (OCP)**: Open for extension, closed for modification
- **Liskov Substitution Principle (LSP)**: Subtypes must be substitutable for their base types
- **Interface Segregation Principle (ISP)**: Clients depend only on interfaces they use
- **Dependency Inversion Principle (DIP)**: Depend on abstractions, not concretions

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ScannerProxy Application                  │
├─────────────────────────────────────────────────────────────┤
│  Main Entry Point (src/main.py)                            │
├─────────────────────────────────────────────────────────────┤
│  Core Services Layer                                        │
│  ├── ScannerService (orchestration)                        │
│  ├── AgentDiscoveryService (network discovery)             │
│  └── FileTransferService (file operations)                 │
├─────────────────────────────────────────────────────────────┤
│  Network Layer                                              │
│  ├── NetworkInterfaceManager (interface detection)         │
│  ├── Scanner Protocol (message handling)                   │
│  └── Message Builder (protocol construction)               │
├─────────────────────────────────────────────────────────────┤
│  Data Transfer Objects (DTOs)                               │
│  └── ScannerProtocolMessage (network models)               │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure & Utilities                                 │
│  ├── Configuration Management                               │
│  ├── Logging System                                         │
│  └── Base Agent Interfaces                                  │
└─────────────────────────────────────────────────────────────┘
```

## System Requirements

### Runtime Requirements

- **Python**: 3.12+ (recommended) or 3.8+ minimum
- **Operating System**: Linux (Ubuntu/Debian preferred), systemd for services
- **Network**: IPv4 network interface with broadcast capability
- **Ports**: UDP 706 and TCP 708 must be available
- **Memory**: 128MB RAM minimum, 256MB recommended for containers
- **Storage**: 500MB free space for application, logs, and received files

### Development Requirements

Additional requirements for development/testing:

- **Docker**: Latest version with docker-compose
- **Make**: GNU Make for automation
- **Git**: Version control and repository management
- **Network Tools**: tcpdump, netstat for debugging (optional)

### Python Dependencies

Current dependencies (from requirements.txt):

```
numpy          # Mathematical operations and data processing
Pillow         # Image processing capabilities  
scapy          # Network packet manipulation (if needed)
pydantic       # Data validation and settings management
netifaces      # Network interface detection
PyYAML         # Configuration file parsing
rich           # Rich CLI interface and progress bars
click          # Command-line interface framework
inquirer       # Interactive command-line prompts
humanize       # Human-readable data formatting
```

### Port Requirements

| Port | Protocol | Purpose | Direction |
|------|----------|---------|-----------|
| 706  | UDP      | Discovery requests, file transfer control | Inbound |
| 708  | TCP      | File data transfer | Inbound |

### Network Configuration

The service requires:
- **Broadcast capability** on the network interface
- **Static IP assignment** recommended for production
- **Firewall rules** allowing inbound UDP 706 and TCP 708
- **DNS resolution** for hostname-based agent addressing (optional)

## Installation & Setup

### Automated Setup (Recommended)

The project includes comprehensive automation through the Makefile:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ScannerProxy
   ```

2. **Quick setup:**
   ```bash
   make setup          # Create venv, install dependencies, check requirements
   make check          # Verify system requirements and configuration
   ```

3. **Development setup:**
   ```bash
   make dev-setup      # Complete development environment with confirmation
   ```

### Manual Installation

1. **Clone and enter directory:**
   ```bash
   git clone <repository-url>
   cd ScannerProxy
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   export SCANNER_CONFIG_ENV=development  # or production
   ```

### Quick Verification

Test the installation:

```bash
make test           # Run basic functionality tests
make lint           # Check code syntax
make mock-scanner   # Interactive testing tool
```

3. **Set up pre-commit hooks:**
   ```bash
   pre-commit install  # if using pre-commit
   ```

## Configuration

### Configuration Files

The application uses YAML configuration files located in the `config/` directory:

- `development.yml` - Development environment settings
- `production.yml` - Production environment settings

### Configuration Structure

```yaml
# Network configuration
network:
  udp_port: 706                    # UDP port for discovery
  tcp_port: 708                    # TCP port for file transfer
  discovery_timeout: 1.0           # Discovery timeout in seconds
  socket_timeout: 1.0              # Socket timeout
  buffer_size: 1024                # Buffer size for network operations
  tcp_chunk_size: 1460             # TCP chunk size for file transfer
  tcp_connection_timeout: 10.0     # TCP connection timeout

# Scanner configuration  
scanner:
  default_src_name: "Scanner-Dev"  # Default source name
  max_retry_attempts: 3            # Maximum retry attempts
  default_file_path: "files/scan.raw"  # Default file to send
  files_directory: "files"         # Directory containing files

# File Transfer Protocol Messages
file_transfer:
  handshake_message: "FILE_TRANSFER_READY"
  size_ok_message: "SIZE_OK"
  complete_message: "FILE_TRANSFER_COMPLETE"
  transfer_ok_message: "TRANSFER_OK"

# Logging configuration
logging:
  level: "DEBUG"                   # Log level
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_enabled: true               # Enable file logging
  file_path: "logs/scanner-dev.log"  # Log file path
  max_file_size: 10485760          # 10MB max file size
  backup_count: 5                  # Number of backup files
  console_enabled: false           # Enable console logging

# Agent configuration
agents:
  discovery_interval: 30.0         # Discovery interval in seconds
  max_agents: 10                   # Maximum number of agents
```

### Environment Variables

- `SCANNER_ENV`: Environment type (`development` or `production`)
- `CONT_IP`: Container IP address (for specific deployment scenarios)
- `DEV_NAME`: Device name
- `DESTINATION`: File destination path

## Core Components

### 1. ScannerService

**Location**: `src/core/scanner_service.py`

Main orchestrator class that coordinates all scanner operations.

**Key Methods**:
- `initialize()`: Initialize network interfaces and services
- `discover_agents()`: Discover available agents on the network
- `send_file_transfer_request()`: Send file transfer requests to agents
- `get_network_status()`: Get current network status

### 2. AgentDiscoveryService

**Location**: `src/network/discovery.py`

Handles network discovery of available agents.

**Key Methods**:
- `discover_agents()`: Broadcast discovery messages and collect responses
- `_build_discovery_message()`: Create discovery protocol messages
- `_listen_for_responses()`: Listen for agent responses

### 3. FileTransferService

**Location**: `src/services/file_transfer.py`

Manages file transfer operations over TCP.

**Key Methods**:
- `send_file_transfer_request()`: Send file transfer request via UDP
- `_initiate_tcp_connection()`: Establish TCP connection for file transfer
- `_send_file_over_tcp()`: Transfer file data over TCP

### 4. NetworkInterfaceManager

**Location**: `src/network/interfaces.py`

Manages network interface detection and configuration.

**Key Methods**:
- `get_default_interface_info()`: Get default network interface details
- `get_network_info()`: Get network information for specific interface
- `list_available_interfaces()`: List all available network interfaces

### 5. ScannerProtocolMessage

**Location**: `src/dto/network_models.py`

Data model for scanner protocol messages with validation.

**Key Features**:
- Message serialization/deserialization
- Field validation
- Protocol constants management

## Network Protocol

### Message Structure

The scanner protocol uses a fixed 90-byte message structure:

```
Offset | Size | Field                | Description
-------|------|----------------------|------------------
0      | 3    | Signature           | 0x55 0x00 0x00
3      | 3    | Type of Request     | Message type
6      | 6    | Reserved1           | Reserved bytes
12     | 4    | Initiator IP        | IPv4 address
16     | 4    | Reserved2           | Reserved bytes
20     | 20   | Source Name         | Source identifier
40     | 40   | Destination Name    | Destination identifier
80     | 10   | Reserved3           | Reserved bytes
```

### Message Types

- **Discovery Request**: `0x5A 0x00 0x00` - Agent discovery
- **File Transfer Request**: `0x5A 0x54 0x00` - File transfer initiation

### Protocol Flow

1. **Discovery Phase**:
   ```
   Scanner --UDP--> Broadcast Discovery (Port 706)
   Agents --UDP--> Response Messages (Port 706)
   ```

2. **File Transfer Phase**:
   ```
   Scanner --UDP--> File Transfer Request (Port 706)
   Agent   --UDP--> Acknowledgment (Port 706)
   Scanner --TCP--> File Data (Port 708)
   ```

## File Structure

```
ScannerProxy/
├── README.md                        # Quick start guide and overview
├── TECHNICAL_DOCUMENTATION.md      # Comprehensive technical documentation
├── README_DISCOVERY_RESPONSE.md    # Agent discovery service details
├── Makefile                        # Automated build and deployment commands
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container image definition
├── docker-compose.yml              # Production container orchestration
├── agent_discovery_app.py          # Main service application entry point
│
├── config/                         # Environment-specific configurations
│   ├── development.yml             # Local development settings
│   ├── production.yml              # Production/container settings
│   └── proxy_test.yml              # Testing configuration
│
├── src/                            # Core application source code
│   ├── __init__.py
│   ├── __main__.py                 # Module entry point for python -m src
│   ├── agents/                     # Agent base classes and interfaces
│   │   ├── __init__.py
│   │   └── base.py
│   ├── core/                       # Core business logic and orchestration
│   │   ├── __init__.py
│   │   └── scanner_service.py      # Main scanner service orchestrator
│   ├── dto/                        # Data transfer objects and models
│   │   ├── __init__.py
│   │   └── network_models.py       # Protocol messages and validation
│   ├── infrastructure/             # Infrastructure layer (future extensions)
│   │   └── __init__.py
│   ├── network/                    # Network layer and protocols
│   │   ├── __init__.py
│   │   ├── discovery.py            # Agent discovery service
│   │   ├── interfaces.py           # Network interface management
│   │   └── protocols/              # Protocol implementations
│   │       ├── __init__.py
│   │       ├── message_builder.py  # Protocol message construction
│   │       └── scanner_protocol.py # Scanner protocol implementation
│   ├── services/                   # Service layer implementations
│   │   ├── __init__.py
│   │   ├── agent_discovery_response.py  # Discovery response service
│   │   └── file_transfer.py        # File transfer service
│   └── utils/                      # Utility modules and helpers
│       ├── __init__.py
│       ├── config.py               # Configuration management
│       └── logging_setup.py        # Logging configuration
│
├── tests/                          # Test suite and testing utilities
│   └── mocks/
│       └── mock_scanner.py         # Interactive scanner testing tool
│
├── scripts/                        # Automation and deployment scripts
│   ├── check.sh                    # System requirements check
│   ├── clean.sh                    # Environment cleanup
│   ├── emergency-stop.sh           # Emergency process termination
│   ├── install-service.sh          # System service installation
│   ├── logs.sh                     # Log viewing utilities
│   ├── remove-service.sh           # Service removal
│   ├── setup.sh                    # Environment setup
│   ├── status.sh                   # Service status checking
│   └── test.sh                     # Test execution
│
├── logs/                           # Application logs and monitoring
│   ├── scanner-dev.log             # Development environment logs
│   └── scanner-prod.log            # Production environment logs
│
└── files/                          # File storage and transfer
    ├── *.raw                       # Received raw scanner files
    └── *.jpg                       # Processed image files (if applicable)
```

### Key Components Description

| Component | Purpose | Location |
|-----------|---------|----------|
| **AgentDiscoveryResponseService** | Handles discovery broadcasts and file transfer requests | `src/services/agent_discovery_response.py` |
| **ScannerService** | Core orchestration and network operations | `src/core/scanner_service.py` |
| **FileTransferService** | File upload/download over TCP | `src/services/file_transfer.py` |
| **NetworkInterfaceManager** | Network interface detection | `src/network/interfaces.py` |
| **ScannerProtocolMessage** | Protocol message parsing | `src/dto/network_models.py` |
| **Mock Scanner** | Interactive testing tool | `tests/mocks/mock_scanner.py` |
| **Configuration System** | YAML-based configuration | `src/utils/config.py` |
| **Logging System** | Structured logging with rotation | `src/utils/logging_setup.py` |
    │   └── mock_scanner.py
    └── unit/
```

## API Documentation

### ScannerService API

```python
from src.core.scanner_service import ScannerService

# Initialize service
service = ScannerService()
service.initialize()

# Discover agents
agents = service.discover_agents()

# Send file transfer request
success, response = service.send_file_transfer_request(
    target_ip="192.168.1.100",
    src_name="MyScanner",
    dst_name="TargetAgent", 
    file_path="files/document.pdf"
)

# Get network status
status = service.get_network_status()
```

### Configuration API

```python
from src.utils.config import config

# Get configuration values
udp_port = config.get('network.udp_port', 706)
timeout = config.get('network.discovery_timeout', 10.0)
src_name = config.get('scanner.default_src_name', 'Scanner')
```

### Protocol Message API

```python
from src.dto.network_models import ScannerProtocolMessage
from src.network.protocols.message_builder import ScannerProtocolMessageBuilder

# Create message using builder
builder = ScannerProtocolMessageBuilder()
message = builder.build_discovery_message("192.168.1.10", "TestScanner")

# Serialize to bytes
data = message.to_bytes()

# Deserialize from bytes
parsed_message = ScannerProtocolMessage.from_bytes(data)

# Debug information
message.debug()
```

## Usage Examples

### Basic Discovery

```python
#!/usr/bin/env python3

from src.core.scanner_service import ScannerService
from src.utils.logging_setup import setup_logging

def main():
    # Setup logging
    setup_logging()
    
    # Initialize scanner service
    scanner = ScannerService()
    scanner.initialize()
    
    # Discover agents
    agents = scanner.discover_agents()
    
    print(f"Found {len(agents)} agents:")
    for message, address in agents:
        src_name = message.src_name.decode('ascii', errors='ignore')
        print(f"- {src_name} at {address}")

if __name__ == "__main__":
    main()
```

### File Transfer

```python
#!/usr/bin/env python3

from src.core.scanner_service import ScannerService
from src.utils.logging_setup import setup_logging

def transfer_file():
    setup_logging()
    
    scanner = ScannerService()
    scanner.initialize()
    
    # Discover agents first
    agents = scanner.discover_agents()
    if not agents:
        print("No agents found")
        return
    
    # Get first agent's IP
    target_ip = agents[0][1].split(':')[0]
    
    # Send file transfer request
    success, response = scanner.send_file_transfer_request(
        target_ip=target_ip,
        file_path="files/scan.raw"
    )
    
    if success:
        print("File transfer completed successfully")
    else:
        print("File transfer failed")

if __name__ == "__main__":
    transfer_file()
```

### Command Line Usage

```bash
# Run the application
python -m src

# Run with specific environment
SCANNER_ENV=production python -m src

# Run mock scanner for testing
python tests/mocks/mock_scanner.py
```

## Testing

### Mock Scanner

The project includes a comprehensive mock scanner for testing:

**Location**: `tests/mocks/mock_scanner.py`

**Features**:
- Interactive CLI menu
- Agent discovery simulation
- File transfer testing
- Metadata response server
- Rich console formatting

**Usage**:
```bash
cd tests/mocks
python mock_scanner.py
```

### Test Network Setup

For testing, you can set up a local network environment:

1. **Start mock scanner in one terminal:**
   ```bash
   python tests/mocks/mock_scanner.py
   ```

2. **Run main application in another terminal:**
   ```bash
   python -m src
   ```

3. **Monitor logs:**
   ```bash
   tail -f logs/scanner-dev.log
   ```

## Deployment

### Automated Deployment (Recommended)

The Makefile provides comprehensive deployment automation:

#### Development Deployment
```bash
make setup          # Set up environment
make service        # Run local service for testing
make mock-scanner   # Interactive testing tool
```

#### Production Deployment
```bash
make prod-deploy    # Complete production setup (Docker + systemd)
make status         # Verify deployment health
make logs           # Monitor service logs
```

#### Container Deployment
```bash
make docker-build   # Build production image
make docker-run     # Start with ipvlan networking
make docker-logs    # Monitor container logs
```

### Manual Development Deployment

1. **Set environment:**
   ```bash
   export SCANNER_CONFIG_ENV=development
   ```

2. **Run agent discovery service:**
   ```bash
   python agent_discovery_app.py
   ```

3. **Alternative module execution:**
   ```bash
   python -m src
   ```

### Manual Production Deployment

#### Option 1: Systemd Service (Automated)
```bash
make install-service    # Uses scripts/install-service.sh
make status            # Check service health
make restart-service   # Restart if needed
```

#### Option 2: Manual Systemd Service

1. **Set environment:**
   ```bash
   export SCANNER_CONFIG_ENV=production
   ```

2. **Create systemd service file:**
   ```ini
   [Unit]
   Description=Scanner Proxy Agent Discovery Service
   After=network.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=scanner
   Group=scanner
   WorkingDirectory=/opt/scannerproxy
   Environment=SCANNER_CONFIG_ENV=production
   Environment=PYTHONPATH=/opt/scannerproxy/src
   ExecStart=/opt/scannerproxy/venv/bin/python agent_discovery_app.py
   Restart=always
   RestartSec=10
   KillMode=process

   # Logging
   StandardOutput=journal
   StandardError=journal
   SyslogIdentifier=scanner-proxy

   # Security
   NoNewPrivileges=true
   PrivateTmp=true
   ProtectSystem=strict
   ReadWritePaths=/opt/scannerproxy/logs /opt/scannerproxy/files

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service:**
   ```bash
   sudo systemctl enable scanner-proxy
   sudo systemctl start scanner-proxy
   sudo systemctl status scanner-proxy
   ```

### Docker Deployment

#### Option 1: Docker Compose (Recommended)
```bash
make docker-build   # Build image
make docker-run     # Start with docker-compose
```

This uses the included `docker-compose.yml` with:
- **ipvlan networking** for direct network access
- **Static IP assignment** (192.168.1.201)
- **Volume mounts** for logs and files
- **Health checks** and automatic restart
- **Resource limits** for production stability

#### Option 2: Manual Docker Deployment

1. **Build image:**
   ```dockerfile
   FROM python:3.12-slim

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY src/ src/
   COPY config/ config/
   COPY agent_discovery_app.py .
   
   RUN mkdir -p logs files
   ENV SCANNER_CONFIG_ENV=production
   
   EXPOSE 706/udp 708/tcp
   
   HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
     CMD pgrep -f "python agent_discovery_app.py" > /dev/null || exit 1
   
   CMD ["python", "agent_discovery_app.py"]
   ```

2. **Build and run:**
   ```bash
   docker build -t scanner-proxy:latest .
   docker run -d \
     --name scanner-proxy-prod \
     --network host \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/files:/app/files \
     -v $(pwd)/config:/app/config:ro \
     --restart unless-stopped \
     scanner-proxy:latest
   ```

### Health Monitoring

Monitor deployment health:

```bash
# Service status
make status

# Real-time logs
make logs
make docker-logs

# Manual checks
sudo systemctl status scanner-proxy
docker ps | grep scanner-proxy
```

### Configuration Management

Update configuration without rebuild:

```bash
# Edit configuration
vim config/production.yml

# Restart service
make restart-service

# Or restart container
make docker-stop
make docker-run
```
   RUN pip install -r requirements.txt

   COPY src/ src/
   COPY config/ config/
   
   ENV SCANNER_ENV=production
   
   CMD ["python", "-m", "src"]
   ```

2. **Build and run:**
   ```bash
   docker build -t scannerproxy .
   docker run -d --name scannerproxy --network host scannerproxy
   ```

## Proxy Mode

### Overview

ScannerProxy supports a powerful proxy mode that automatically forwards received files to other network agents. This enables creating a network of interconnected scanner agents for distributed file processing workflows.

### Configuration

Enable proxy mode in the configuration file:

```yaml
# config/production.yml or config/development.yml
proxy:
  enabled: true                    # Enable proxy mode
  agent_ip_address: "192.168.1.138"  # Target agent IP for forwarding

scanner:
  default_src_name: "Scanner-Proxy"  # Identifier for this proxy agent
  files_directory: "files"           # Local storage for received files
```

### How Proxy Mode Works

1. **Scanner connects to proxy agent** (this service)
2. **Proxy receives file** via TCP and stores locally  
3. **Proxy automatically forwards** the file to the configured target agent
4. **Target agent processes** the file normally
5. **Local copy is retained** according to retention policy

### Proxy Flow Diagram

```
Scanner          Proxy Agent         Target Agent
   |    UDP/TCP      |    UDP/TCP         |
   |---------------->|---------------->   |
   |   File Transfer |   File Forward     |
   |                 |                    |
   |    [Local Storage + Forward]         |
```

### Use Cases

- **Legacy Integration**: Connect old scanners to modern processing systems
- **Load Balancing**: Distribute files across multiple processing agents  
- **Network Bridging**: Route files between different network segments
- **Backup & Redundancy**: Maintain local copies while forwarding for processing
- **Protocol Translation**: Convert between different scanner protocols

### Proxy Agent Configuration Example

```yaml
# Proxy agent that receives from scanners and forwards to processing server
network:
  udp_port: 706
  tcp_port: 708

scanner:
  default_src_name: "Network-Proxy-01"
  files_directory: "files"
  max_files_retention: 50

proxy:
  enabled: true
  agent_ip_address: "192.168.1.200"  # Processing server

logging:
  level: "INFO"
  file_path: "logs/proxy-agent.log"
```

### Monitoring Proxy Operations

Monitor proxy forwarding through logs:

```bash
# View proxy forwarding activity
grep "Proxy mode:" logs/scanner-prod.log

# Monitor successful forwards
grep "Proxy file transfer completed" logs/scanner-prod.log

# Check for forwarding errors
grep "Proxy file transfer failed" logs/scanner-prod.log
```

### Advanced Proxy Features

- **Automatic Retry**: Failed forwards are logged but don't prevent local storage
- **File Retention**: Local files follow standard retention policies
- **Error Handling**: Network failures don't interrupt scanner operations
- **Progress Tracking**: Detailed logging of forward operations
- **Configuration Reload**: Proxy settings can be updated without restart

## Troubleshooting

### Common Issues

1. **Network Interface Detection Fails**
   - Check network interface availability
   - Verify IPv4 configuration
   - Ensure broadcast capability

2. **Discovery Timeout**
   - Increase `network.discovery_timeout` in config
   - Check firewall settings for UDP port 706
   - Verify network connectivity

3. **File Transfer Fails**
   - Check TCP port 708 accessibility
   - Verify file permissions and existence
   - Monitor logs for detailed error messages

4. **Permission Errors**
   - Ensure read permissions on files directory
   - Check write permissions on logs directory
   - Verify network interface access permissions

### Debugging

1. **Enable debug logging:**
   ```yaml
   logging:
     level: "DEBUG"
     console_enabled: true
   ```

2. **Monitor network traffic:**
   ```bash
   sudo tcpdump -i any port 706 or port 708
   ```

3. **Check application logs:**
   ```bash
   tail -f logs/scanner-dev.log
   ```

### Log Analysis

**Common log patterns:**

- **Successful discovery:** `Discovery completed. Found N agents`
- **Network initialization:** `Scanner service initialized on interface`
- **File transfer start:** `Sending file transfer request to`
- **TCP connection:** `TCP connection established with`

## Maintenance

### Log Rotation

Logs are automatically rotated based on configuration:
- Maximum file size: 10MB (development) / 50MB (production)
- Backup count: 5 (development) / 10 (production)

### Configuration Updates

1. **Modify configuration files in `config/` directory**
2. **Restart application to apply changes**
3. **Monitor logs for configuration errors**

### Performance Monitoring

Monitor these metrics:
- Discovery response time
- File transfer speed
- Memory usage
- Network interface utilization

## Security Considerations

1. **Network Security**
   - Use firewall rules to restrict access to ports 706 and 708
   - Consider VPN for remote access
   - Monitor network traffic for anomalies

2. **File Security**
   - Validate file types before transfer
   - Implement file size limits
   - Use secure file storage locations

3. **Application Security**
   - Run with minimal required privileges
   - Regular security updates for dependencies
   - Input validation for all external data

## Extension Points

### Adding New Message Types

1. **Define new message type constant in `ProtocolConstants`**
2. **Add builder method in `ScannerProtocolMessageBuilder`**
3. **Implement handler logic in relevant service**

### Custom Agent Types

1. **Extend `BaseAgent` class in `src/agents/base.py`**
2. **Implement required abstract methods**
3. **Register agent type in service layer**

### Protocol Extensions

1. **Extend message structure in `ScannerProtocolMessage`**
2. **Update serialization/deserialization logic**
3. **Maintain backward compatibility**

---

This documentation provides a complete reference for rebuilding and extending the ScannerProxy project. For specific implementation details, refer to the inline code documentation and comments within each module.
