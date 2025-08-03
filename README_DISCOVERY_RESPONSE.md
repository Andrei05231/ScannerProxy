# Agent Discovery Response Service

This application implements the agent side of the scanner communication protocol - it listens for scanner discovery broadcasts and responds to them, then handles file transfer requests. The service supports two operational modes: **Agent mode** (with raw file conversion) and **Proxy mode** (for forwarding to other agents).

## Purpose

While `tests/mocks/mock_scanner.py` acts as a scanner that **sends** discovery broadcasts and waits for responses, the main application (`agent_discovery_app.py`) acts as an agent that **receives** discovery broadcasts and **sends** responses back.

### Service Behavior
- **Listens for UDP discovery broadcasts** on port 706
- **Responds with agent information** including capabilities and identity
- **Accepts file transfer requests** via UDP on port 706
- **Receives file data** via TCP on port 708
- **Converts raw scanner files** to standard formats (JPG, PNG, PDF) in Agent mode
- **Forwards received files** to other agents in Proxy mode

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
- **Raw File Conversion**: Converts proprietary scanner formats to standard formats (JPG, PNG, PDF)
- **Dual Operational Modes**: Agent mode (conversion) or Proxy mode (forwarding)
- **Smart File Management**: Raw files stored in `files/raw/`, converted files in `files/`
- **Real-time Logging**: Comprehensive logging of all discovery, transfer, and conversion operations
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
   - **Processing**: Service analyzes raw file format and converts to standard format (Agent mode)
   - **Storage**: Raw files saved in `files/raw/`, converted files in `files/`
   - **Forwarding**: Service optionally forwards files if in Proxy mode

### Expected Log Output
```
2025-01-02 10:30:15 - Discovery request received from Scanner-Dev at 192.168.1.137:45678
2025-01-02 10:30:15 - Discovery response sent to 192.168.1.137:45678
2025-01-02 10:30:20 - File transfer request received from Scanner-Dev at 192.168.1.137:45679  
2025-01-02 10:30:20 - TCP connection accepted from 192.168.1.137:52341
2025-01-02 10:30:20 - Starting file transfer from 192.168.1.137:52341
2025-01-02 10:30:21 - File transfer completed: received_file_20250102_103020_192_168_1_137.raw (1048576 bytes)
2025-01-02 10:30:21 - Operating in Agent mode - converting raw file
2025-01-02 10:30:21 - Raw file analysis: Format=Color JPG, Quality=High, Width=1200
2025-01-02 10:30:21 - Converted to: received_file_20250102_103020_192_168_1_137.jpg
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

# Agent identification and operation
scanner:
  default_src_name: "Scanner-Prod"  # Agent name in responses
  files_directory: "files"          # Directory for converted files
  raw_files_directory: "files/raw"  # Directory for received raw files
  max_files_retention: 10           # Automatic cleanup threshold
  operational_mode: "agent"         # "agent" for conversion, "proxy" for forwarding

# Raw file conversion settings (Agent mode)
conversion:
  default_output_format: "jpg"      # jpg, png, or pdf
  jpg_quality: 85                   # JPEG quality (1-100)
  png_compression: 6                # PNG compression (0-9)

# Proxy mode (Proxy mode only)
proxy:
  enabled: false                    # Enable when operational_mode is "proxy"
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
- **Phase 3**: Receives file data and saves with timestamp-based naming in `files/raw/`
- **Phase 4**: **Agent Mode**: Analyzes raw file format and converts to standard format in `files/`
- **Phase 5**: **Proxy Mode**: Forwards raw file to configured target agent

### Raw File Processing (Agent Mode)
The service automatically detects and converts proprietary scanner formats:

**Supported Formats**:
- **Black & White**: 1-bit monochrome scans → JPG/PNG
- **Grayscale**: 8-bit grayscale scans → JPG/PNG  
- **Color**: 24-bit RGB color scans → JPG/PNG
- **PDF Documents**: PDF-encoded content → PDF files

**Conversion Process**:
1. **Header Analysis**: Reads 16-byte scanner format header
2. **Format Detection**: Identifies scan type, quality, and pixel dimensions
3. **Data Extraction**: Processes binary pixel data according to format
4. **Image Generation**: Creates standard format files with PIL/Pillow
5. **Quality Control**: Applies configurable quality settings for output

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
│  ├── Save Raw Files in files/raw/                          │
│  └── Route to Agent or Proxy Processing                    │
├─────────────────────────────────────────────────────────────┤
│  Agent Mode Processing                                      │
│  ├── Raw File Format Analysis                              │
│  ├── Scanner Format Conversion                             │
│  ├── Standard Format Output (JPG/PNG/PDF)                  │
│  └── Quality Control & Optimization                        │
├─────────────────────────────────────────────────────────────┤
│  Proxy Mode Processing                                      │
│  ├── Target Agent Discovery                                │
│  ├── File Forwarding Logic                                 │
│  └── Network Bridge Operations                             │
├─────────────────────────────────────────────────────────────┤
│  File Management                                            │
│  ├── Dual Directory Structure (raw/ & converted)           │
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
- **RawFileConverter**: Scanner format analysis and conversion engine
- **Configuration System**: Same YAML-based configuration management
- **Logging System**: Consistent structured logging with rotation

### Threading Model
- **Main Thread**: Service coordination and signal handling
- **UDP Listener Thread**: Discovery request handling and response sending
- **TCP Listener Thread**: File transfer connection acceptance
- **File Transfer Threads**: Individual file transfer handling (one per connection)
- **Conversion Threads**: Raw file processing in Agent mode (asynchronous)

## Operational Modes

The service supports two distinct operational modes configured via `scanner.operational_mode`:

### Agent Mode (`operational_mode: "agent"`)
**Purpose**: Convert proprietary scanner files to standard formats

**Workflow**:
1. **Receive**: Raw scanner files via network transfer
2. **Store**: Save raw files in `files/raw/` directory
3. **Analyze**: Parse scanner format headers and detect content type
4. **Convert**: Transform to standard formats (JPG, PNG, PDF)
5. **Output**: Save converted files in `files/` directory

**Use Cases**:
- **Document Processing**: Convert scanner output for document management systems
- **Image Processing**: Prepare files for image processing pipelines
- **Format Standardization**: Ensure consistent file formats across systems
- **Legacy Integration**: Bridge old scanners with modern applications

### Proxy Mode (`operational_mode: "proxy"`)
**Purpose**: Forward received files to other network agents

**Workflow**:
1. **Receive**: Files from scanners (raw or any format)
2. **Store**: Temporarily cache files locally
3. **Forward**: Send files to configured target agent
4. **Monitor**: Log transfer operations and success rates

**Use Cases**:
- **Network Bridging**: Connect scanners across network segments
- **Load Balancing**: Distribute files across multiple processing agents
- **Geographic Distribution**: Forward files to remote processing centers
- **Backup Systems**: Maintain copies while forwarding to primary systems

### Configuration Examples

**Agent Mode Configuration** (`config/development.yml`):
```yaml
scanner:
  operational_mode: "agent"
  files_directory: "files"
  raw_files_directory: "files/raw"

conversion:
  default_output_format: "jpg"
  jpg_quality: 85
```

**Proxy Mode Configuration** (`config/production.yml`):
```yaml
scanner:
  operational_mode: "proxy"
  files_directory: "files"

proxy:
  enabled: true
  agent_ip_address: "192.168.1.138"
```

## Proxy Mode Integration

## Advanced Proxy Mode Configuration

When proxy mode is enabled, the service operates as an intelligent network bridge with additional features:

### Enhanced Proxy Workflow
1. **Receive File**: Normal file reception from scanner
2. **Store Locally**: Save file with standard naming convention  
3. **Target Discovery**: Verify target agent availability
4. **Forward File**: Automatically send file to configured target agent
5. **Confirmation**: Wait for acknowledgment from target agent
6. **Log Operations**: Comprehensive logging of all proxy operations

### Proxy Failover & Reliability
```yaml
proxy:
  enabled: true
  agent_ip_address: "192.168.1.138"
  fallback_agents: ["192.168.1.139", "192.168.1.140"]  # Optional fallback list
  retry_attempts: 3                                     # Retry failed forwards
  timeout: 30                                          # Forward timeout (seconds)
```

### Proxy Use Cases
- **Network Bridging**: Connect scanners to processing systems on different networks
- **Load Distribution**: Distribute files across multiple processing agents
- **Legacy Integration**: Bridge old scanners with modern processing infrastructure
- **Backup & Processing**: Maintain local copies while forwarding for processing

## Testing Raw File Conversion

### Manual Conversion Testing
```bash
# Test conversion with standalone utility
python convert_raw.py files/raw/test_scan.raw

# Test specific format conversion
python convert_raw.py files/raw/color_scan.raw files/output.png --quality 95

# Batch test multiple files
for file in files/raw/*.raw; do
    python convert_raw.py "$file"
done
```

### Integration Testing with Mock Scanner
```bash
# Start service in Agent mode
python agent_discovery_app.py

# Send test raw files via mock scanner
python -m tests.mocks.mock_scanner
# Select: "Send File Transfer Request"
# Choose raw files from files/ directory

# Verify conversion results
ls -la files/raw/     # Check received raw files
ls -la files/         # Check converted output files
```

### Format Verification
```bash
# Check file formats
file files/converted_*.jpg
file files/converted_*.png  
file files/converted_*.pdf

# Verify image properties
identify files/converted_*.jpg    # ImageMagick tool
```

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
ls -la files/ files/raw/

# Monitor disk space
df -h

# Check directory structure
find files -type d -exec ls -ld {} \;
```

#### File Conversion Issues
```bash
# Check raw file format
python -c "
from src.services.raw_converter import RawFileConverter
converter = RawFileConverter()
analysis = converter.analyze_raw_file('files/raw/problematic.raw')
print(f'Analysis: {analysis}')
"

# Verify PIL/Pillow installation
python -c "from PIL import Image; print('PIL OK')"

# Check conversion logs
grep -i "conversion\|convert" logs/scanner-dev.log

# Test conversion manually
python convert_raw.py files/raw/problematic.raw --debug
```

#### Operational Mode Issues
```bash
# Check current mode
grep "operational_mode" config/development.yml

# Verify mode detection in logs
grep "Operating in.*mode" logs/scanner-dev.log

# Test mode switching
# Edit config file and restart service
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

def custom_conversion_callback(raw_file_path, converted_file_path, analysis):
    # Custom post-conversion processing
    return {"conversion_complete": True}

# Register callbacks
service.set_discovery_callback(custom_discovery_callback)
service.set_file_transfer_callback(custom_file_transfer_callback)
service.set_conversion_callback(custom_conversion_callback)
```

### Service Extensions
- **Raw File Processing**: Custom format support and conversion pipelines
- **File Processing**: Add post-conversion file processing pipelines
- **Quality Enhancement**: AI-powered image enhancement and optimization
- **Format Detection**: Advanced file type analysis and validation
- **External Notifications**: Send notifications to external systems
- **Custom Protocols**: Extend to support additional message types
- **Metrics Collection**: Add performance and usage metrics

### Integration Examples
- **Database Integration**: Log transfers and conversions to database
- **Cloud Storage**: Forward converted files to cloud storage services
- **Document Management**: Integration with DMS systems for processed files
- **Image Processing**: Connect to OCR and image analysis services
- **Message Queues**: Integrate with RabbitMQ, Redis, etc.
- **Web APIs**: HTTP callbacks for transfer and conversion notifications

---

This agent discovery response service provides a robust, production-ready foundation for scanner network integration with comprehensive raw file conversion, dual operational modes, flexible configuration, and extensive monitoring capabilities.
