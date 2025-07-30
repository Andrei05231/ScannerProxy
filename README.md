# ScannerProxy

A modular network scanner proxy application built with Python, following SOLID principles and clean architecture patterns.

## Overview

ScannerProxy is a network discovery and communication tool that enables scanner devices to discover and communicate with document processing agents on a network. The application has been completely refactored from a monolithic structure to a modular, maintainable architecture with comprehensive test coverage.

## Features

- 🔍 **Network Agent Discovery**: Automatically discover document processing agents on the network
- 🌐 **Cross-Platform Network Detection**: Uses `netifaces` for reliable network interface detection
- ✅ **IP Address Validation**: Proper IPv4 validation with 4-byte network representation
- 🏗️ **SOLID Architecture**: Clean separation of concerns following SOLID principles
- 🔧 **Builder Pattern**: Flexible message construction with validation
- ⚙️ **Environment Configuration**: YAML-based configuration for different environments
- 📝 **Comprehensive Logging**: Structured logging with configurable levels
- 🧪 **90% Test Coverage**: Extensive unit and integration test suite
- 🔨 **Development Tools**: Comprehensive Makefile with testing, formatting, and deployment targets

## Architecture

The project follows SOLID principles with clear separation of concerns:

```
src/
├── core/                   # Business Logic Layer
│   └── scanner_service.py  # Main orchestration service (DIP)
├── network/                # Network Layer
│   ├── interfaces.py       # Network interface management
│   ├── discovery.py        # Agent discovery service
│   └── protocols/          # Protocol implementations
│       ├── message_builder.py     # Message construction (Builder pattern)
│       └── scanner_protocol.py    # Protocol serialization/deserialization
├── dto/                    # Data Transfer Objects
│   └── network_models.py   # Pydantic models with validation
├── services/               # Service Layer
│   └── file_transfer.py    # File transfer operations
├── utils/                  # Utilities
│   ├── config.py          # Configuration management
│   └── logging_setup.py   # Logging configuration
└── agents/                 # Agent Interfaces
    └── base.py            # Base classes and protocols
```

### SOLID Principles Applied

- **SRP**: Each class has a single responsibility
- **OCP**: Open for extension, closed for modification
- **LSP**: Proper inheritance hierarchies
- **ISP**: Segregated interfaces for different concerns
- **DIP**: Dependency injection throughout the system

## Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Setup with Makefile

```bash
# Clone the repository
git clone https://github.com/Andrei05231/ScannerProxy.git
cd ScannerProxy

# Complete development setup (creates venv, installs all dependencies)
make setup

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the application
make run

# Run tests
make test

# Show all available commands
make help
```

### Manual Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Andrei05231/ScannerProxy.git
   cd ScannerProxy
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

#### Using Makefile (Recommended)
```bash
make run               # Run in default mode
make run-dev          # Run in development mode
make run-prod         # Run in production mode
make local-server     # Run local development server
```

#### Direct Python Execution
```bash
python3 run.py                    # Main entry point
python3 -m src                    # Module execution
python3 tests/mocks/mock_scanner.py  # Demo/Testing
```

### Configuration

Configuration is managed through YAML files in the `config/` directory:

- `config/development.yml` - Development environment settings
- `config/production.yml` - Production environment settings

Example configuration:
```yaml
network:
  udp_port: 706
  tcp_port: 708
  discovery_timeout: 10.0
  socket_timeout: 1.0
  buffer_size: 1024

scanner:
  default_src_name: "Scanner"
  max_retry_attempts: 3
  default_file_path: "files/scan.raw"

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_enabled: true
  file_path: "logs/scanner.log"
```

Set environment with:
```bash
export SCANNER_ENV=development  # or production
```

## Testing

### Quick Testing Commands

```bash
make test              # Run all tests
make test-unit         # Run unit tests only
make test-integration  # Run integration tests only
make test-coverage     # Run tests with coverage report
make test-watch        # Run tests in watch mode
```

### Specific Test Categories

```bash
make test-config       # Configuration management tests
make test-scanner      # Scanner service tests
make test-network      # Network discovery and interface tests
make test-protocols    # Message protocol tests
make test-file-transfer # File transfer service tests
```

### Coverage Reports

```bash
make test-coverage     # HTML + terminal coverage report
make test-coverage-xml # XML coverage report (CI/CD)
```

Coverage reports are generated in:
- HTML: `htmlcov/index.html`
- XML: `coverage.xml`
- Terminal: Displayed during test run

### Test Structure

```
tests/
├── unit/                    # Unit tests (90%+ coverage)
│   ├── test_config.py          # Configuration management
│   ├── test_scanner_service.py # Main service logic
│   ├── test_network_models.py  # Data models
│   ├── test_discovery.py       # Network discovery
│   ├── test_network_interfaces.py # Network interfaces
│   ├── test_message_protocols.py  # Protocol handling
│   └── test_file_transfer.py   # File operations
├── integration/             # Integration tests
├── mocks/                   # Mock implementations
│   └── mock_scanner.py      # Scanner simulation
└── conftest.py             # Test fixtures and configuration
```

### Test Features

- **Comprehensive Mocking**: Isolated unit tests with proper mocking
- **Property-Based Testing**: Edge case validation
- **Integration Testing**: End-to-end workflow validation
- **Performance Testing**: Network timeout and error handling
- **Coverage Tracking**: Detailed coverage reports with missing line identification

## API Reference

### ScannerService

Main orchestration service following dependency injection principles.

```python
from src.core.scanner_service import ScannerService

# Initialize service
scanner_service = ScannerService()
scanner_service.initialize()

# Get network status
status = scanner_service.get_network_status()
print(f"Local IP: {status['local_ip']}")

# Discover agents
agents = scanner_service.discover_agents()
```

### Network Interface Management

```python
from src.network.interfaces import NetworkInterfaceManager

manager = NetworkInterfaceManager()
interface_info = manager.get_default_interface_info()
print(f"Interface: {interface_info['name']}")
print(f"IP Address: {interface_info['ip_address']}")
print(f"Broadcast: {interface_info['broadcast']}")
```

### Message Building

```python
from src.network.protocols.message_builder import ScannerProtocolMessageBuilder
from ipaddress import IPv4Address

builder = ScannerProtocolMessageBuilder()
message = (builder
           .with_signature(b'SCAN')
           .with_src_name(b"MyScanner")
           .with_dst_name(b"DocumentAgent")
           .with_initiator_ip(IPv4Address("192.168.1.100"))
           .build())
```

### Protocol Serialization

```python
from src.network.protocols.scanner_protocol import MessageSerializer, MessageDeserializer

# Serialize message
serialized_data = MessageSerializer.serialize_message(message)

# Deserialize message
received_message = MessageDeserializer.deserialize_message(serialized_data)
```

### Configuration Management

```python
from src.utils.config import config

# Get configuration values
udp_port = config.get('network.udp_port', 706)
timeout = config.get('network.discovery_timeout', 10.0)
log_level = config.get('logging.level', 'INFO')

# Access nested configuration
network_config = config.get('network')
```

### Agent Discovery

```python
from src.network.discovery import AgentDiscoveryService

discovery_service = AgentDiscoveryService()
agents = discovery_service.discover_agents(
    timeout=10.0,
    src_name="MyScanner"
)

for agent in agents:
    print(f"Found agent: {agent.src_name} at {agent.initiator_ip}")
```

### File Transfer

```python
from src.services.file_transfer import FileTransferService

file_service = FileTransferService()

# Send file transfer request
success = file_service.send_file_transfer_request(
    target_ip="192.168.1.100",
    file_path="files/scan.raw",
    src_name="Scanner",
    dst_name="Agent"
)

if success:
    # Initiate TCP connection and transfer
    file_service.initiate_tcp_connection(
        target_ip="192.168.1.100",
        file_path="files/scan.raw"
    )
```

## Development

### Development Workflow

#### Setting Up Development Environment

```bash
# Complete setup
make setup

# Install additional development tools
make install-dev-deps

# Format code
make format

# Run linting
make lint

# Run all quality checks
make check
```

#### Code Quality Standards

```bash
make format            # Format with black and isort
make lint             # Run flake8 and mypy checks
make check            # Run all quality checks
```

#### Testing Workflow

```bash
# Basic testing
make test             # Run all tests
make test-unit        # Unit tests only
make test-watch       # Continuous testing

# Coverage analysis
make test-coverage    # Generate coverage reports
open htmlcov/index.html  # View coverage in browser

# Specific component testing
make test-config      # Test configuration module
make test-protocols   # Test message protocols
```

#### Pre-commit Workflow

```bash
make pre-commit       # Run all pre-commit checks
make ci-test         # Run CI/CD pipeline tests
```

### Project Structure

```
ScannerProxy/
├── src/                    # Source code
│   ├── core/              # Business logic
│   ├── network/           # Network operations
│   ├── services/          # Service implementations
│   ├── dto/               # Data transfer objects
│   ├── utils/             # Utilities
│   └── agents/            # Agent interfaces
├── tests/                  # Test files
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── mocks/             # Mock implementations
│   └── conftest.py        # Test configuration
├── config/                 # Configuration files
│   ├── development.yml    # Dev configuration
│   └── production.yml     # Prod configuration
├── scripts/               # Utility scripts
├── logs/                  # Log files
├── files/                 # Data files
├── requirements.txt       # Python dependencies
├── pytest.ini           # Test configuration
├── Dockerfile            # Docker image
├── docker-compose.yaml   # Docker orchestration
├── Makefile             # Development commands
├── run.py               # Main entry point
└── README.md            # This file
```

### Key Components

#### 1. Scanner Service (`src/core/scanner_service.py`)
- Main business logic orchestration
- Dependency injection container
- Network status management
- Agent discovery coordination

#### 2. Network Discovery (`src/network/discovery.py`)
- Agent discovery protocol implementation
- UDP broadcast handling
- Response parsing and validation
- Timeout and retry management

#### 3. Protocol Messages (`src/dto/network_models.py`)
- Pydantic models with validation
- IPv4 address handling with 4-byte packing
- Message serialization/deserialization
- Protocol constants and enums

#### 4. Message Builder (`src/network/protocols/message_builder.py`)
- Builder pattern implementation
- Fluent interface for message construction
- Validation and error handling
- Method chaining support

#### 5. Configuration (`src/utils/config.py`)
- YAML-based configuration loading
- Environment-specific settings
- Default value handling
- Dot notation access

#### 6. File Transfer (`src/services/file_transfer.py`)
- UDP request/response handling
- TCP file transfer implementation
- Progress tracking
- Error handling and recovery

### Testing Architecture

#### Unit Tests
- **Isolated Testing**: Each component tested in isolation
- **Comprehensive Mocking**: External dependencies mocked
- **Edge Case Coverage**: Boundary conditions and error scenarios
- **Property Validation**: Input validation and type checking

#### Integration Tests
- **End-to-End Workflows**: Complete application flows
- **Network Simulation**: Mock network environments
- **File System Operations**: Temporary file handling
- **Configuration Testing**: Different environment scenarios

#### Test Utilities
- **Fixtures**: Reusable test data and mocks
- **Helpers**: Common testing utilities
- **Mock Services**: Simulated external services
- **Test Data**: Sample messages and configurations

### Docker Support

#### Building Images

```bash
make build            # Build main image
make build-test       # Build test image
make build-all        # Build all images
```

#### Running Containers

```bash
make run-container    # Run main container
make run-test-container # Run test container
make run-test-debug   # Debug test container
```

#### Docker Compose

```bash
make up              # Start all services
make down            # Stop all services
make restart         # Restart services
make logs            # View service logs
```

#### Network Setup

```bash
make create-network  # Create Docker network
make remove-network  # Remove Docker network
```

### Maintenance and Cleanup

```bash
make clean           # Clean all artifacts
make clean-test      # Clean test artifacts
make clean-build     # Clean build artifacts
make clean-docker    # Clean Docker images
make clean-logs      # Clean log files
```

### Security and Dependencies

```bash
make security-check  # Run security audit
make update-deps     # Update dependencies
make freeze-deps     # Freeze current versions
```

### Utility Commands

```bash
make show-config     # Show current configuration
make show-structure  # Show project tree
make help           # Show all available commands
```

## Dependencies

- **pydantic**: Data validation and parsing
- **netifaces**: Cross-platform network interface detection  
- **PyYAML**: YAML configuration file parsing
- **Standard Library**: socket, struct, threading, logging

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow SOLID principles and maintain clean architecture
4. Add tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Maintain SOLID principles
- Add docstrings for public methods
- Keep functions focused and small

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### v2.0.0 - Architecture Refactor
- ✅ Complete refactor following SOLID principles
- ✅ Proper IPv4 address validation with 4-byte packing
- ✅ Modular network detection using netifaces
- ✅ Builder pattern for message construction
- ✅ Dependency injection throughout the system
- ✅ Environment-specific configuration
- ✅ Comprehensive error handling and logging

### v1.0.0 - Initial Implementation
- Basic scanner proxy functionality
- Monolithic architecture
- Hardcoded network assumptions

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.

---

**Built with ❤️ using SOLID principles and clean architecture patterns**
