# Agent Discovery Response Service

This application implements the agent side of the scanner communication protocol - it listens for scanner discovery broadcasts and responds to them, then handles file transfer requests.

## Purpose

While `tests/mocks/mock_scanner.py` acts as a scanner that **sends** discovery broadcasts and waits for responses, the main application (`agent_discovery_app.py`) acts as an agent that **receives** discovery broadcasts and **sends** responses back.

### Service Behavior
- **Listens for UDP discovery broadcasts** on port 706
- **Responds with agent information** including capabilities and identity
- **Accepts file transfer requests** via UDP on port 706
- **Receives file data** via TCP on port 708
- **Supports proxy mode** to forward received files to other agents

## Usage

### Option 1: Direct execution
```bash
python agent_discovery_app.py
```

### Option 2: Module execution
```bash
python -m agent_discovery_app
```

### Option 3: Automated execution
```bash
make service        # Local development service
make prod-deploy    # Production deployment with Docker/systemd
```

## Features

- **Headless Service**: Runs as a background service without user interaction
- **Automatic Discovery Response**: Responds to all valid scanner discovery broadcasts
- **File Transfer Reception**: Handles complete file transfer workflow (UDP request → TCP data)
- **Proxy Mode Support**: Can forward received files to other network agents
- **Real-time Logging**: Comprehensive logging of all discovery and transfer operations
- **Network Auto-Configuration**: Automatic network interface detection and setup
- **Graceful Shutdown**: Proper cleanup on exit or signal interruption (Ctrl+C)
- **File Management**: Automatic file retention and cleanup policies

## Testing with Mock Scanner

### Complete Testing Workflow

1. **Start the agent discovery service:**
   ```bash
   python agent_discovery_app.py
   ```
   
   The service will output:
   ```
   Scanner agent initialized on interface eth0 (192.168.1.XXX)
   UDP listener started on 192.168.1.XXX:706
   TCP listener started on 192.168.1.XXX:708
   Agent discovery response service is running...
   ```

2. **In another terminal, run the mock scanner:**
   ```bash
   python -m tests.mocks.mock_scanner
   ```
   
   Select menu options:
   - **"Discover Agents"** → Should find the running service
   - **"Send File Transfer Request"** → Should successfully transfer files

3. **Observe the complete interaction:**
   - **Discovery Phase**: Mock scanner broadcasts → Service responds with agent info
   - **File Transfer Phase**: Mock scanner sends file request → Service acknowledges
   - **Data Transfer**: Mock scanner opens TCP connection → Service receives file data
   - **Storage/Forwarding**: Service saves file locally and optionally forwards if in proxy mode

### Expected Log Output
```
2025-01-02 10:30:15 - Discovery request received from Scanner-Dev at 192.168.1.137:45678
2025-01-02 10:30:15 - Discovery response sent to 192.168.1.137:45678
2025-01-02 10:30:20 - File transfer request received from Scanner-Dev at 192.168.1.137:45679  
2025-01-02 10:30:20 - TCP connection accepted from 192.168.1.137:52341
2025-01-02 10:30:20 - Starting file transfer from 192.168.1.137:52341
2025-01-02 10:30:21 - File transfer completed: received_file_20250102_103020_192_168_1_137.raw (1048576 bytes)
```

## Configuration

The service uses the same configuration system as the entire project:

### Configuration Files
- **Development**: `config/development.yml` - Used when `SCANNER_CONFIG_ENV=development` 
- **Production**: `config/production.yml` - Used in Docker containers and system service
- **Environment Detection**: Automatically selects based on `SCANNER_CONFIG_ENV` environment variable

### Key Configuration Settings

```yaml
# Network configuration
network:
  udp_port: 706                    # Discovery and control messages
  tcp_port: 708                    # File data transfer
  discovery_timeout: 1.0           # Response timeout
  tcp_connection_timeout: 10.0     # TCP connection timeout

# Agent identification
scanner:
  default_src_name: "Scanner-Prod"  # Agent name in responses
  files_directory: "files"          # Directory for received files
  max_files_retention: 10           # Automatic cleanup threshold

# Proxy mode (optional)
proxy:
  enabled: true                     # Enable automatic file forwarding
  agent_ip_address: "192.168.1.138"  # Target agent for forwarding

# Logging
logging:
  level: "INFO"                     # Log detail level
  file_path: "logs/scanner-prod.log"  # Log file location
  console_enabled: false            # Console output (dev only)
```

## Protocol Support

The service implements the complete scanner protocol specification:

### 1. Discovery Request (`0x5A 0x00 0x00`)
- **Behavior**: Responds with agent information and capabilities
- **Response**: Uses configured agent name and network details
- **Logging**: Records all discovery requests with sender information

### 2. File Transfer Request (`0x5A 0x54 0x00`)  
- **Phase 1**: Acknowledges UDP request and prepares for file reception
- **Phase 2**: Accepts TCP connection on configured port
- **Phase 3**: Receives file data and saves with timestamp-based naming
- **Phase 4**: Optional proxy forwarding if enabled

### Message Format
All messages follow the 90-byte scanner protocol format:
```
Bytes 0-2:   Signature (0x55 0x00 0x00)
Bytes 3-5:   Message Type (0x5A 0x00 0x00 or 0x5A 0x54 0x00)
Bytes 6-11:  Reserved fields
Bytes 12-15: Initiator IP address
Bytes 16-19: Additional reserved fields
Bytes 20-39: Source name (20 bytes)
Bytes 40-79: Destination name (40 bytes)
Bytes 80-89: Final reserved fields
```

## Service Architecture

### Component Interaction
```
┌─────────────────────────────────────────────────────────────┐
│                AgentDiscoveryResponseService                │
├─────────────────────────────────────────────────────────────┤
│  UDP Listener Thread (Port 706)                            │
│  ├── Discovery Requests → Build & Send Response            │
│  └── File Transfer Requests → Start TCP Listener           │
├─────────────────────────────────────────────────────────────┤
│  TCP File Receiver Thread (Port 708)                       │
│  ├── Accept Client Connections                             │
│  ├── Receive File Data in Chunks                           │
│  ├── Save with Timestamp Naming                            │
│  └── Optional Proxy Forwarding                             │
├─────────────────────────────────────────────────────────────┤
│  File Management                                            │
│  ├── Automatic Retention Policy                            │
│  ├── Timestamp-based Naming                                │
│  └── Directory Management                                   │
└─────────────────────────────────────────────────────────────┘
```

### Code Reuse & Architecture

This service maximizes code reuse from the existing codebase:

- **ScannerProtocolMessage**: Same message parsing and building logic
- **ScannerProtocolMessageBuilder**: Consistent message construction
- **NetworkInterfaceManager**: Identical network detection and configuration
- **Configuration System**: Same YAML-based configuration management
- **Logging System**: Consistent structured logging with rotation

### Threading Model
- **Main Thread**: Service coordination and signal handling
- **UDP Listener Thread**: Discovery request handling and response sending
- **TCP Listener Thread**: File transfer connection acceptance
- **File Transfer Threads**: Individual file transfer handling (one per connection)

## Proxy Mode Integration

When proxy mode is enabled, the service operates as an intelligent network bridge:

### Proxy Workflow
1. **Receive File**: Normal file reception from scanner
2. **Store Locally**: Save file with standard naming convention
3. **Forward File**: Automatically send file to configured target agent
4. **Log Operations**: Comprehensive logging of all proxy operations

### Proxy Configuration
```yaml
proxy:
  enabled: true                     # Enable proxy forwarding
  agent_ip_address: "192.168.1.138"  # Target agent IP
```

### Proxy Use Cases
- **Network Bridging**: Connect scanners to processing systems on different networks
- **Load Distribution**: Distribute files across multiple processing agents
- **Legacy Integration**: Bridge old scanners with modern processing infrastructure
- **Backup & Processing**: Maintain local copies while forwarding for processing

## Error Handling & Recovery

### Network Error Handling
- **UDP Timeout**: Graceful handling of network timeouts
- **TCP Connection Errors**: Automatic connection cleanup
- **Interface Detection Failures**: Fallback to default interface

### File Transfer Error Handling
- **Partial Transfers**: Detection and cleanup of incomplete files
- **Disk Space**: Monitoring and error reporting for storage issues
- **Permission Errors**: Clear error messages for file system issues

### Service Recovery
- **Graceful Shutdown**: Signal handling for clean service termination
- **Resource Cleanup**: Proper socket and file handle cleanup
- **Restart Capability**: Designed for automatic restart by systemd

## Monitoring & Troubleshooting

### Service Health Monitoring
```bash
# Check if service is running
make status

# View real-time logs
make logs

# Monitor file transfer activity
tail -f logs/scanner-prod.log | grep "File transfer"

# Check network connectivity
sudo netstat -tulpn | grep -E ':(706|708)'
```

### Common Issues & Solutions

#### Service Won't Start
```bash
# Check port availability
sudo netstat -tulpn | grep -E ':(706|708)'

# Check configuration
python -c "from src.utils.config import config; print(config.data)"

# Check logs for errors
tail -20 logs/scanner-dev.log
```

#### Discovery Not Working
```bash
# Check network interface
ip addr show

# Test UDP port
sudo tcpdump -i any port 706

# Verify configuration
grep -A5 "network:" config/development.yml
```

#### File Transfer Issues
```bash
# Check TCP port
sudo tcpdump -i any port 708

# Verify file permissions
ls -la files/

# Monitor disk space
df -h
```

## Extension Points

### Custom Callbacks
The service supports custom callback functions for extended functionality:

```python
def custom_discovery_callback(message, sender_address):
    # Custom discovery processing
    return {"custom": "data"}

def custom_file_transfer_callback(message, sender_address):  
    # Custom file transfer processing
    return {"processed": True}

# Register callbacks
service.set_discovery_callback(custom_discovery_callback)
service.set_file_transfer_callback(custom_file_transfer_callback)
```

### Service Extensions
- **File Processing**: Add post-receive file processing pipelines
- **External Notifications**: Send notifications to external systems
- **Custom Protocols**: Extend to support additional message types
- **Metrics Collection**: Add performance and usage metrics

### Integration Examples
- **Database Integration**: Log transfers to database
- **Cloud Storage**: Forward files to cloud storage services
- **Message Queues**: Integrate with RabbitMQ, Redis, etc.
- **Web APIs**: HTTP callbacks for transfer notifications

---

This agent discovery response service provides a robust, production-ready foundation for scanner network integration with comprehensive testing tools, flexible configuration, and extensive monitoring capabilities.
