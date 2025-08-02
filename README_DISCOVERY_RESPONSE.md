# Agent Discovery Response Service

This application is the counterpart to the mock scanner - it listens for scanner discovery broadcasts and automatically responds to them.

## Purpose

While `tests/mocks/mock_scanner.py` acts as a scanner that **sends** discovery broadcasts and waits for responses, this application acts as an agent that **receives** discovery broadcasts and **sends** responses back.

## Usage

### Option 1: Run directly
```bash
python agent_discovery_app.py
```

### Option 2: Run as module
```bash
python -m agent_discovery_app
```

## Features

- **Headless Service**: Runs as a background service without user interaction
- **Discovery Response**: Automatically responds to scanner discovery broadcasts
- **File Transfer Reception**: Listens for file transfer requests and receives files via TCP
- **Real-time Logging**: Shows live discovery requests and file transfers in logs
- **Network Configuration**: Automatic network interface detection
- **Graceful Shutdown**: Proper cleanup on exit or signal interruption

## Testing with Mock Scanner

1. **Start the discovery response service:**
   ```bash
   python agent_discovery_app.py
   ```

2. **In another terminal, run the mock scanner:**
   ```bash
   python -m tests.mocks.mock_scanner
   # Select "Discover Agents" option
   # Then select "Send File Transfer Request"
   ```

3. **Observe the interaction:**
   - Mock scanner sends discovery broadcast → Service responds
   - Mock scanner sends file transfer request (UDP) → Service acknowledges
   - Mock scanner opens TCP connection → Service receives file data
   - Service saves received file locally

## Configuration

The service uses the same configuration system as the main application:

- **Development**: `config/development.yml`
- **Production**: `config/production.yml`
- **Environment variable**: `SCANNER_ENV` (defaults to "development")

Key configuration values:
- `network.udp_port`: Port to listen on for discovery/file transfer requests
- `network.tcp_port`: Port to listen on for file data transfer
- `scanner.default_src_name`: Agent name to include in responses
- `scanner.files_directory`: Directory to save received files

## Protocol Support

The service supports two types of scanner protocol messages:

1. **Discovery Request** (`0x5A 0x00 0x00`):
   - Responds with agent information
   - Uses configured agent name as destination

2. **File Transfer Request** (`0x5A 0x54 0x00`):
   - Acknowledges the request via UDP
   - Starts TCP listener on configured port
   - Receives and saves file data locally

## Architecture

The service follows the same SOLID principles as the main application:

```
AgentDiscoveryResponseService
├── UDP Listener (port 706)
│   ├── Discovery Requests → Send Response
│   └── File Transfer Requests → Start TCP Listener
└── TCP File Receiver (port 708)
    ├── Accept connections
    ├── Receive file data
    └── Save to local directory
```

## Code Reuse

This implementation maximizes code reuse from the existing codebase:

- **ScannerProtocolMessage**: Same message parsing/building
- **ScannerProtocolMessageBuilder**: Same message construction
- **NetworkInterfaceManager**: Same network detection
- **Configuration system**: Same YAML-based config
- **Logging system**: Same structured logging

## Extension Points

The service includes a callback mechanism for custom handling:

```python
def custom_discovery_callback(message: ScannerProtocolMessage, sender_address: str):
    # Custom logic when discovery request received
    # Can log, process, or modify response behavior
    return {"custom": "data"}

discovery_service.set_discovery_callback(custom_discovery_callback)
```
