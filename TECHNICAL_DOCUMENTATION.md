# ScannerProxy Technical Documentation

## Project Overview

ScannerProxy is a Python-based application that facilitates network-based scanner communication and document transfer operations. The system implements a modular architecture following SOLID design principles and provides both scanner discovery and file transfer capabilities over UDP/TCP protocols.

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
12. [Troubleshooting](#troubleshooting)

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

- **Python**: 3.8+ (tested with Python 3.12)
- **Operating System**: Linux (Ubuntu/Debian recommended)
- **Network**: IPv4 network interface with broadcast capability
- **Memory**: Minimum 128MB RAM
- **Storage**: 100MB free space for application and logs

### Python Dependencies

```
numpy>=1.20.0
Pillow>=8.0.0
scapy>=2.4.0
pydantic>=1.8.0
netifaces>=0.11.0
PyYAML>=5.4.0
rich>=10.0.0
click>=8.0.0
inquirer>=2.7.0
humanize>=3.0.0
```

## Installation & Setup

### Option 1: Standard Installation

1. **Clone the repository:**
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

4. **Set environment variables (optional):**
   ```bash
   export SCANNER_ENV=development  # or production
   ```

### Option 2: Development Setup

1. **Follow steps 1-3 from Standard Installation**

2. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt  # if exists
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
├── requirements.txt                 # Python dependencies
├── config/                         # Configuration files
│   ├── development.yml
│   └── production.yml
├── docs/                          # Documentation
├── files/                         # Sample files for transfer
│   ├── scan.raw
│   └── other_scan.raw
├── logs/                          # Application logs
├── src/                           # Source code
│   ├── __init__.py
│   ├── __main__.py               # Application entry point
│   ├── main.py                   # Main application logic
│   ├── connect_to_scanner.py     # Scanner connection utilities
│   ├── convert_raw_data.py       # Raw data conversion
│   ├── receiver_proxy.py         # Receiver proxy functionality
│   ├── scanner_proxy.py          # Scanner proxy functionality
│   ├── agents/                   # Agent base classes
│   │   ├── __init__.py
│   │   └── base.py
│   ├── core/                     # Core business logic
│   │   ├── __init__.py
│   │   └── scanner_service.py
│   ├── dto/                      # Data transfer objects
│   │   ├── __init__.py
│   │   └── network_models.py
│   ├── infrastructure/           # Infrastructure components
│   │   └── __init__.py
│   ├── network/                  # Network layer
│   │   ├── __init__.py
│   │   ├── discovery.py
│   │   ├── interfaces.py
│   │   └── protocols/
│   │       ├── __init__.py
│   │       ├── message_builder.py
│   │       └── scanner_protocol.py
│   ├── server/                   # Server components
│   ├── services/                 # Service layer
│   │   ├── __init__.py
│   │   └── file_transfer.py
│   └── utils/                    # Utility modules
│       ├── __init__.py
│       ├── config.py
│       └── logging_setup.py
└── tests/                        # Test suite
    ├── mocks/
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

### Development Deployment

1. **Set environment:**
   ```bash
   export SCANNER_ENV=development
   ```

2. **Run application:**
   ```bash
   python -m src
   ```

### Production Deployment

1. **Set environment:**
   ```bash
   export SCANNER_ENV=production
   ```

2. **Create systemd service (optional):**
   ```ini
   [Unit]
   Description=Scanner Proxy Service
   After=network.target

   [Service]
   Type=simple
   User=scanner
   WorkingDirectory=/opt/scannerproxy
   Environment=SCANNER_ENV=production
   ExecStart=/opt/scannerproxy/venv/bin/python -m src
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service:**
   ```bash
   sudo systemctl enable scannerproxy
   sudo systemctl start scannerproxy
   ```

### Docker Deployment

1. **Create Dockerfile:**
   ```dockerfile
   FROM python:3.12-slim

   WORKDIR /app
   COPY requirements.txt .
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
