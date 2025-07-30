# ScannerProxy Documentation

## Module Documentation
### src/dto/network_models.py
"""
Network-related data models and DTOs.
Follows SRP - Single responsibility for network data structures.
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, field_validator
from typing import ClassVar, Protocol
from ipaddress import IPv4Address, AddressValueError


class ProtocolConstants:
    """Constants for the scanner protocol - SRP: Single responsibility for constants"""
    SIGNATURE: bytes = b'\x55\x00\x00'
    TYPE_OF_REQUEST: bytes = b'\x5a\x00\x00'
    TYPE_OF_FILE_TRANSFER: bytes = b'\x5a\x54\x00'  # New request type for file transfer
    EXPECTED_MESSAGE_SIZE: int = 90
    SRC_NAME_SIZE: int = 20
    DST_NAME_SIZE: int = 40
    RESERVED1_SIZE: int = 6
    RESERVED2_SIZE: int = 4
### src/dto/__init__.py
### src/services/__init__.py
"""Services package"""
### src/services/file_transfer.py
"""
File transfer service implementation.
Follows SRP - Single responsibility for file transfer operations.
Uses the same pattern as AgentDiscoveryService for consistency.
"""
import socket
import logging
import time
from typing import Tuple, Optional, List
from ipaddress import IPv4Address

from ..dto.network_models import ScannerProtocolMessage, ProtocolConstants
from ..network.protocols.message_builder import ScannerProtocolMessageBuilder
from ..utils.config import config


class FileTransferService:
    """
    Handles file transfer operations - SRP: Single responsibility for file transfer
    Follows the same pattern as AgentDiscoveryService for code reusability
### src/__main__.py
"""
Module entry point for running the scanner proxy application.
"""
import sys
from main import main

if __name__ == "__main__":
    sys.exit(main())
### src/main.py
"""
Main application module.
"""
import logging
from .core.scanner_service import ScannerService
from .utils.config import config
from .utils.logging_setup import setup_logging


def print_discovery_summary(discovered_agents):
    """Print a summary of discovered agents"""
    print("\n=== DISCOVERY SUMMARY ===")
    if discovered_agents:
        print(f"Found {len(discovered_agents)} agent(s) listening for scanned documents:")
        for i, (message, address) in enumerate(discovered_agents, 1):
            print(f"{i}. Agent at {address}")
            print(f"   Source Name: {message.src_name.decode('ascii', errors='ignore')}")
            print(f"   Destination Name: {message.dst_name.decode('ascii', errors='ignore')}")
            print(f"   IP: {message.initiator_ip}")
    else:
### src/utils/__init__.py
### src/utils/logging_setup.py
"""
Logging setup utility.
Configures file and console logging based on configuration settings.
"""
import logging
import logging.handlers
import os
from pathlib import Path
from .config import config


def setup_logging() -> None:
    """
    Setup logging based on configuration settings.
    Supports both file and console logging with rotation.
    """
    # Get logging configuration
    log_level = config.get('logging.level', 'INFO')
    log_format = config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_enabled = config.get('logging.file_enabled', True)
### src/utils/config.py
"""
Configuration management system.
Follows SRP - Single responsibility for configuration.
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigurationManager:
    """Manages application configuration with environment-specific settings"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.environment = os.getenv("SCANNER_ENV", "development")
        self._config_cache: Optional[Dict[str, Any]] = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration for the current environment"""
### src/scanner_proxy.py
import socket
import struct
import threading
from datetime import datetime

# === CONFIGURATION ===
SCANNER_SUBNET = "10.0.52."
SCANNER_PORT = 706
RECEIVER_IP = "192.168.50.173"
RECEIVER_PORT = 706
RECEIVER_TCP_PORT = 708
LOCAL_TCP_PORT = 708

scanner_udp_addr = None  # ('ip', port)

def create_response_packet(scanner_mac, scanner_ip, device_name="Custom-Scan"):
    now = datetime.now()
    header = bytes.fromhex(
        "55 00 00 5a 00 00 00 09 b9 00 a5 2c 0a 00 34 74 "
        "00 00 02 c4 4c 6d 33 36 00 00 00 00 00 00 00 00 "
### src/core/__init__.py
"""Core business logic package"""
### src/core/scanner_service.py
"""
Main scanner service orchestrator.
Follows SRP - Single responsibility for coordinating scanner operations.
Follows DIP - Depends on abstractions, not concretions.
"""
from typing import List, Tuple, Dict, Any, Optional
import logging

from ..network.interfaces import NetworkInterfaceManager
from ..network.discovery import AgentDiscoveryService
from ..services.file_transfer import FileTransferService
from ..dto.network_models import ScannerProtocolMessage
from ..utils.config import config


class ScannerService:
    """
    Main service that orchestrates scanner operations.
    Follows DIP by depending on abstractions (interfaces) rather than concrete implementations.
    """
### src/__init__.py
### src/agents/__init__.py
### src/agents/base.py
"""
Base agent interfaces and abstract classes.
Follows LSP - Liskov Substitution Principle and ISP - Interface Segregation Principle.
"""
from abc import ABC, abstractmethod
from typing import Protocol, Any, Dict


class Discoverable(Protocol):
    """Interface for discoverable agents - ISP: Interface segregation"""
    def respond_to_discovery(self, discovery_message: Any) -> Any:
        """Respond to a discovery request"""
        ...


class DocumentHandler(Protocol):
    """Interface for document handling - ISP: Interface segregation"""
    def handle_document(self, document: Any) -> bool:
        """Handle incoming document"""
        ...
### src/infrastructure/__init__.py
"""Infrastructure package"""
### src/convert_raw_data.py
import sys
import struct
import numpy as np
from PIL import Image
from datetime import datetime
import os

# Destination path setup
fileDestination = os.environ['DESTINATION']
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filePath = f'/srv/scans/{fileDestination}/converted_{timestamp}.png'

# Input check
if len(sys.argv) < 2:
    print("Usage: python convertRawData.py <input_file>")
    sys.exit(1)

file = sys.argv[1]

# Drift parameter (adjust if necessary)
### src/receiver_proxy.py
from scapy.all import *
import re
import time

def parse_hex_dump(hex_string):
    lines = hex_string.strip().splitlines()
    cleaned_lines = []
    for line in lines:
        # Remove line number offset at start
        line = re.sub(r"^\s*[0-9a-fA-F]{4,5}\s*", "", line)
        cleaned_lines.append(line)
    joined = " ".join(cleaned_lines)
    hex_bytes = re.findall(r'[0-9a-fA-F]{2}', joined)
    return bytes.fromhex(''.join(hex_bytes))

def modify_packet(raw_bytes, src_mac, dst_mac, src_ip, dst_ip):
    pkt = Ether(raw_bytes)
    pkt.src = src_mac
    pkt.dst = dst_mac
    if IP in pkt:
### src/connect_to_scanner.py
import socket
import struct
import time
import os
from datetime import datetime
import sys
import threading
import subprocess


listening_enabled = threading.Event()
listening_enabled.set()  

sys.stdout.reconfigure(line_buffering=True)

containerIp = os.environ[ 'CONT_IP' ]
deviceName = os.environ['DEV_NAME']
fileDestination = os.environ['DESTINATION']

# containerIp = '10.0.52.111'
### src/network/interfaces.py
"""
Network interface detection and management.
Follows SRP - Single responsibility for network interface operations.
"""
from typing import Tuple
import ipaddress
import netifaces


class NetworkInterfaceManager:
    """Manages network interface detection and configuration."""
    
    @staticmethod
    def get_default_interface_info() -> Tuple[str, str, str]:
        """
        Get local IP, broadcast IP, and interface name from the default network interface.
        
        Returns:
            Tuple of (local_ip, broadcast_ip, interface_name)
        """
### src/network/__init__.py
"""Network layer package"""
### src/network/protocols/scanner_protocol.py
"""
Scanner protocol implementation.
Follows SRP - Single responsibility for protocol operations.
"""
from ipaddress import IPv4Address
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...dto.network_models import ScannerProtocolMessage, ProtocolConstants

# Import at runtime to avoid circular imports
def get_protocol_constants():
    from ...dto.network_models import ProtocolConstants
    return ProtocolConstants

def get_scanner_protocol_message():
    from ...dto.network_models import ScannerProtocolMessage
    return ScannerProtocolMessage


### src/network/protocols/message_builder.py
"""
Message builder for scanner protocol messages.
Follows SRP - Single responsibility for building messages.
"""
from ipaddress import IPv4Address
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...dto.network_models import ScannerProtocolMessage, ProtocolConstants

from ...utils.config import config

def get_protocol_constants():
    from ...dto.network_models import ProtocolConstants
    return ProtocolConstants

def get_scanner_protocol_message():
    from ...dto.network_models import ScannerProtocolMessage
    return ScannerProtocolMessage

### src/network/protocols/__init__.py
"""Protocol implementations package"""
### src/network/discovery.py
"""
Agent discovery service.
Follows SRP - Single responsibility for network discovery operations.
"""
from typing import List, Tuple
import socket
import time

from ..dto.network_models import ScannerProtocolMessage
from ..network.protocols.message_builder import ScannerProtocolMessageBuilder
from ..utils.config import config


class AgentDiscoveryService:
    """Service for discovering agents on the network."""
    
    def __init__(self, local_ip: str, broadcast_ip: str, port: int):
        self.local_ip = local_ip
        self.broadcast_ip = broadcast_ip
        self.port = port
