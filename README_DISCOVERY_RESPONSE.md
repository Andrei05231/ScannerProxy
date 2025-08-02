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

- **Interactive CLI**: Rich console interface with menu-driven operation
- **Real-time Discovery Events**: Shows live discovery requests as they arrive
- **Service Management**: Start/stop the discovery response service
- **Network Configuration**: Automatic network interface detection
- **Graceful Shutdown**: Proper cleanup on exit or signal interruption

## Testing with Mock Scanner

1. **Start the discovery response service:**
   ```bash
   python agent_discovery_app.py
   # Select "Start Discovery Response Service"
   ```

2. **In another terminal, run the mock scanner:**
   ```bash
   python -m tests.mocks.mock_scanner
   # Select "Discover Agents" option
   ```

3. **Observe the interaction:**
   - Mock scanner sends discovery broadcast
   - Discovery response service receives the broadcast
   - Response service automatically sends back a discovery response
   - Mock scanner receives and displays the response

## Configuration

The service uses the same configuration system as the main application:

- **Development**: `config/development.yml`
- **Production**: `config/production.yml`
- **Environment variable**: `SCANNER_ENV` (defaults to "development")

Key configuration values:
- `network.udp_port`: Port to listen on (default: 706)
- `scanner.default_src_name`: Agent name to include in responses

## Architecture

The service follows the same SOLID principles as the main application:

```
AgentDiscoveryResponseService
├── Listens on UDP port 706 (configurable)
├── Parses incoming ScannerProtocolMessage
├── Validates discovery request type (0x5A 0x00 0x00)
├── Builds discovery response message
└── Sends response back to original sender
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
