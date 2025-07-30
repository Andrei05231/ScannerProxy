# ScannerProxy

A modular network scanner proxy application built with Python, following SOLID principles and clean architecture patterns.

## Overview

ScannerProxy is a network discovery and communication tool that enables scanner devices to discover and communicate with document processing agents on a network. The application has been completely refactored from a monolithic structure to a modular, maintainable architecture.

## Features

- 🔍 **Network Agent Discovery**: Automatically discover document processing agents on the network
- 🌐 **Cross-Platform Network Detection**: Uses `netifaces` for reliable network interface detection
- ✅ **IP Address Validation**: Proper IPv4 validation with 4-byte network representation
- 🏗️ **SOLID Architecture**: Clean separation of concerns following SOLID principles
- 🔧 **Builder Pattern**: Flexible message construction with validation
- ⚙️ **Environment Configuration**: YAML-based configuration for different environments
- 📝 **Comprehensive Logging**: Structured logging with configurable levels

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
├── dto/                    # Data Transfer Objects
│   └── network_models.py   # Pydantic models with validation
├── utils/                  # Utilities
│   └── config.py          # Configuration management
└── agents/                 # Agent Interfaces
    └── base.py            # Base classes and protocols
```

### SOLID Principles Applied

- **SRP**: Each class has a single responsibility
- **OCP**: Open for extension, closed for modification
- **LSP**: Proper inheritance hierarchies
- **ISP**: Segregated interfaces for different concerns
- **DIP**: Dependency injection throughout the system

## Installation

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Setup

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

There are multiple ways to run the application:

#### 1. Main Entry Point (Recommended)
```bash
python3 run.py
```

#### 2. Module Execution
```bash
python3 -m src
```

#### 3. Demo/Testing
```bash
python3 tests/mocks/mock_scanner.py
```

### Configuration

Configuration is managed through YAML files in the `config/` directory:

- `config/development.yml` - Development environment settings
- `config/production.yml` - Production environment settings

Example configuration:
```yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

network:
  discovery_timeout: 10.0
  scanner_port: 706
  
scanner:
  default_name: "Scanner"
  broadcast_interval: 5.0
```

## API Reference

### ScannerService

Main orchestration service following dependency injection principles.

```python
from core.scanner_service import ScannerService

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
from network.interfaces import NetworkInterfaceManager

manager = NetworkInterfaceManager()
interface_info = manager.get_default_interface_info()
```

### Message Building

```python
from network.protocols.message_builder import ScannerProtocolMessageBuilder

builder = ScannerProtocolMessageBuilder()
message = (builder
           .set_source_name("MyScanner")
           .set_destination_name("DocumentAgent")
           .set_initiator_ip("192.168.1.100")
           .build())
```

## Development

### Project Structure

```
ScannerProxy/
├── src/                    # Source code
├── tests/                  # Test files
│   └── mocks/             # Mock implementations
├── config/                 # Configuration files
├── scripts/               # Utility scripts
├── requirements.txt       # Python dependencies
├── run.py                 # Main entry point
└── README.md              # This file
```

### Key Components

1. **Scanner Service** (`src/core/scanner_service.py`)
   - Main business logic orchestration
   - Dependency injection container
   - Network status management

2. **Network Discovery** (`src/network/discovery.py`)
   - Agent discovery protocol implementation
   - UDP broadcast handling
   - Response parsing and validation

3. **Protocol Messages** (`src/dto/network_models.py`)
   - Pydantic models with validation
   - IPv4 address handling with 4-byte packing
   - Message serialization/deserialization

4. **Configuration** (`src/utils/config.py`)
   - YAML-based configuration loading
   - Environment-specific settings
   - Default value handling

### Testing

Run the mock scanner to test the system:

```bash
python3 tests/mocks/mock_scanner.py
```

This will:
- Initialize the scanner service
- Display network interface information
- Attempt to discover agents on the network
- Show a summary of discovered agents

## Docker Support

The project includes Docker support for containerized deployment:

```bash
# Build the image
docker build -t scanner-proxy .

# Run with docker-compose
docker-compose up
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
