# ScannerProxy - Project Overview

## Executive Summary

ScannerProxy is a sophisticated Python-based network service that enables seamless scanner discovery and file transfer operations across network environments. The system bridges legacy scanner infrastructure with modern processing workflows through a dual-mode architecture supporting both standalone file storage and intelligent proxy forwarding.

## Key Capabilities

### Core Features
- **Network Agent Discovery**: Automated scanner/agent discovery via UDP broadcasts
- **Secure File Transfer**: Reliable TCP-based file transmission with progress tracking
- **Dual Operation Modes**: Standalone storage or intelligent proxy forwarding
- **Rich Interactive Testing**: Full-featured CLI testing tools with progress visualization
- **Production Ready**: Complete Docker containerization and systemd service integration

### Advanced Features  
- **Automatic File Forwarding**: Proxy mode forwards received files to target agents
- **File Retention Management**: Configurable cleanup policies for received files
- **Network Interface Detection**: Automatic interface discovery and configuration
- **Health Monitoring**: Built-in health checks and comprehensive logging
- **Configuration Management**: Environment-specific YAML configuration system

## Architecture Overview

### System Design
The application follows SOLID design principles with a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    ScannerProxy Service                     │
├─────────────────────────────────────────────────────────────┤
│  Entry Points                                               │
│  ├── agent_discovery_app.py (Main service)                 │
│  └── tests/mocks/mock_scanner.py (Testing tool)            │
├─────────────────────────────────────────────────────────────┤
│  Service Layer                                              │
│  ├── AgentDiscoveryResponseService (Discovery & File RX)   │
│  ├── ScannerService (Core orchestration)                   │
│  └── FileTransferService (File operations)                 │
├─────────────────────────────────────────────────────────────┤
│  Network Layer                                              │
│  ├── UDP Discovery Protocol (Port 706)                     │
│  ├── TCP File Transfer (Port 708)                          │
│  └── Network Interface Management                          │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├── Protocol Message Parsing                              │
│  ├── Configuration Management                              │
│  └── File Storage & Retention                              │
└─────────────────────────────────────────────────────────────┘
```

### Communication Flow

#### Discovery Phase
```
Scanner → UDP Broadcast (706) → Agent → UDP Response (706) → Scanner
```

#### File Transfer Phase  
```
Scanner → UDP File Request (706) → Agent → UDP ACK (706) → Scanner
Scanner → TCP File Data (708) → Agent → [Storage/Forward] → Target
```

## Project Structure

### Core Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Main Service** | Agent discovery and file reception | `agent_discovery_app.py` |
| **Mock Scanner** | Interactive testing and validation | `tests/mocks/mock_scanner.py` |
| **Discovery Service** | Network discovery and response handling | `src/services/agent_discovery_response.py` |
| **Scanner Service** | Core business logic orchestration | `src/core/scanner_service.py` |
| **File Transfer** | TCP file operations | `src/services/file_transfer.py` |
| **Network Management** | Interface detection and configuration | `src/network/interfaces.py` |
| **Protocol Implementation** | Message parsing and validation | `src/dto/network_models.py` |

### Automation & DevOps

| Tool | Purpose | Location |
|------|---------|----------|
| **Makefile** | Build and deployment automation | `Makefile` |
| **Docker Setup** | Container orchestration | `Dockerfile`, `docker-compose.yml` |
| **System Scripts** | Service management automation | `scripts/` |
| **Configuration** | Environment-specific settings | `config/` |

## Operational Modes

### 1. Standalone Mode
- **Purpose**: Direct file storage and processing
- **Use Case**: Simple scanner integration, file archival
- **Configuration**: `proxy.enabled: false`
- **Behavior**: Stores received files locally with retention management

### 2. Proxy Mode  
- **Purpose**: Intelligent file forwarding to target agents
- **Use Case**: Network bridging, load balancing, legacy integration
- **Configuration**: `proxy.enabled: true`, `proxy.agent_ip_address: "target_ip"`
- **Behavior**: Receives files locally then automatically forwards to configured agent

## Deployment Options

### Development Environment
```bash
make setup          # Environment setup
make service        # Local service execution
make mock-scanner   # Interactive testing
```

### Production Deployment
```bash
make prod-deploy    # Complete production setup
make status         # Health monitoring  
make logs           # Log monitoring
```

### Container Deployment
```bash
make docker-build   # Build production image
make docker-run     # Start with networking
make docker-logs    # Container monitoring
```

## Configuration Management

### Environment-Specific Configuration
- **Development**: `config/development.yml` - Debug logging, local testing
- **Production**: `config/production.yml` - Production logging, performance optimization
- **Custom**: Environment variable `SCANNER_CONFIG_ENV` controls selection

### Key Configuration Areas
- **Network Settings**: Ports, timeouts, buffer sizes
- **Proxy Configuration**: Target agents, forwarding behavior  
- **File Management**: Storage directories, retention policies
- **Logging**: Levels, rotation, output destinations
- **Agent Identity**: Service naming and identification

## Network Protocol

### Protocol Specification
- **Message Format**: Fixed 90-byte binary protocol
- **Discovery Message**: `0x5A 0x00 0x00` - Agent discovery requests
- **File Transfer Message**: `0x5A 0x54 0x00` - File transfer initiation
- **Transport**: UDP for control, TCP for data

### Network Requirements
- **UDP Port 706**: Discovery and control messages
- **TCP Port 708**: File data transfer
- **Broadcast Capability**: Required for discovery operations
- **Static IP**: Recommended for production proxy mode

## Testing & Validation

### Interactive Testing
The `mock_scanner.py` tool provides comprehensive testing capabilities:
- **Agent Discovery**: Simulate scanner discovery broadcasts
- **File Transfer**: Test complete file transfer workflows
- **Network Visualization**: Rich CLI with progress tracking
- **Error Simulation**: Test error handling and recovery

### Automated Testing
```bash
make test           # Functional tests
make lint           # Code quality checks
make check          # System requirements validation
```

## Monitoring & Maintenance

### Health Monitoring
- **Service Status**: `make status` - systemd and Docker health
- **Log Monitoring**: `make logs` - filtered application logs
- **Network Monitoring**: Built-in connection tracking

### Maintenance Operations
- **Service Control**: `make restart-service` - graceful restart
- **Emergency Stop**: `make emergency-stop` - force termination
- **Environment Reset**: `make clean` - complete cleanup

### Log Management
- **Structured Logging**: JSON-formatted logs with rotation
- **Environment-Specific**: Different log levels per environment
- **Retention**: Automatic log rotation and cleanup

## Security Considerations

### Network Security
- **Firewall Configuration**: Restrict access to ports 706/708
- **Network Segmentation**: Consider VPN for remote access
- **Traffic Monitoring**: Log and monitor all network activity

### Application Security
- **File Validation**: Input validation for all received files
- **Resource Limits**: Container resource constraints
- **User Permissions**: Run with minimal required privileges

### Operational Security
- **Configuration Protection**: Read-only configuration mounts
- **Log Security**: Secure log storage and access
- **Update Management**: Regular dependency updates

## Extension Points

### Protocol Extensions
- **New Message Types**: Extend protocol for additional operations
- **Custom Agents**: Implement specialized agent behaviors
- **Protocol Versioning**: Support multiple protocol versions

### Service Extensions
- **Custom Processing**: Add file processing pipelines
- **External Integrations**: Connect to external systems
- **Monitoring Integration**: Add metrics and alerting

### Deployment Extensions  
- **Multi-Container**: Scale with multiple container instances
- **Load Balancing**: Distribute across multiple proxy agents
- **High Availability**: Implement redundancy and failover

## Conclusion

ScannerProxy represents a production-ready solution for modern scanner network integration. Its modular architecture, comprehensive testing tools, and flexible deployment options make it suitable for both simple file storage scenarios and complex multi-agent processing workflows. The system's emphasis on automation, monitoring, and maintainability ensures reliable operation in production environments.

For detailed implementation information, refer to:
- **[README.md](README.md)**: Quick start guide and basic operations
- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)**: Complete technical reference
- **[README_DISCOVERY_RESPONSE.md](README_DISCOVERY_RESPONSE.md)**: Service-specific documentation
