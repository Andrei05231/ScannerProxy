"""
Shared test fixtures and utilities for the ScannerProxy test suite.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from ipaddress import IPv4Address
import tempfile
import os
from typing import List, Tuple

from src.dto.network_models import ScannerProtocolMessage, ProtocolConstants
from src.core.scanner_service import ScannerService
from src.network.discovery import AgentDiscoveryService
from src.services.file_transfer import FileTransferService


@pytest.fixture
def mock_logger():
    """Provide a mock logger"""
    return Mock()


@pytest.fixture
def sample_ip():
    """Provide a sample IP address"""
    return IPv4Address("192.168.1.100")


@pytest.fixture
def sample_protocol_message():
    """Provide a sample protocol message"""
    return ScannerProtocolMessage(
        signature=ProtocolConstants.SIGNATURE,
        type_of_request=ProtocolConstants.TYPE_OF_REQUEST,
        initiator_ip=IPv4Address("192.168.1.100"),
        src_name=b"TestSource",
        dst_name=b"TestDestination"
    )


@pytest.fixture
def sample_file_transfer_message():
    """Provide a sample file transfer protocol message"""
    return ScannerProtocolMessage(
        signature=ProtocolConstants.SIGNATURE,
        type_of_request=ProtocolConstants.TYPE_OF_FILE_TRANSFER,
        initiator_ip=IPv4Address("192.168.1.100"),
        src_name=b"TestSource",
        dst_name=b"TestDestination"
    )


@pytest.fixture
def temp_file():
    """Provide a temporary file for testing"""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        f.write("Test file content for unit testing")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def temp_directory():
    """Provide a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_network_interface():
    """Mock network interface information"""
    return ("192.168.1.100", "192.168.1.255", "eth0")


@pytest.fixture
def mock_config():
    """Mock configuration with common test values"""
    config_data = {
        'network.udp_port': 706,
        'network.tcp_port': 708,
        'network.discovery_timeout': 5.0,
        'scanner.default_src_name': 'TestScanner',
        'scanner.default_file_path': 'test_scan.raw',
        'logging.level': 'DEBUG',
        'logging.file_path': 'test_logs/test.log'
    }
    
    with patch('src.utils.config.config') as mock:
        mock.get.side_effect = lambda key, default=None: config_data.get(key, default)
        yield mock


@pytest.fixture
def mock_scanner_service():
    """Provide a mock scanner service"""
    service = Mock(spec=ScannerService)
    service.local_ip = "192.168.1.100"
    service.broadcast_ip = "192.168.1.255"
    service.interface_name = "eth0"
    service.discovery_service = Mock()
    service.file_transfer_service = Mock()
    return service


@pytest.fixture
def mock_discovered_agents():
    """Provide mock discovered agents"""
    agent1 = ScannerProtocolMessage(
        signature=ProtocolConstants.SIGNATURE,
        type_of_request=ProtocolConstants.TYPE_OF_REQUEST,
        initiator_ip=IPv4Address("192.168.1.101"),
        src_name=b"Agent1",
        dst_name=b"Scanner"
    )
    
    agent2 = ScannerProtocolMessage(
        signature=ProtocolConstants.SIGNATURE,
        type_of_request=ProtocolConstants.TYPE_OF_REQUEST,
        initiator_ip=IPv4Address("192.168.1.102"),
        src_name=b"Agent2",
        dst_name=b"Scanner"
    )
    
    return [
        (agent1, "192.168.1.101:706"),
        (agent2, "192.168.1.102:706")
    ]


@pytest.fixture
def mock_socket():
    """Provide a mock socket"""
    socket_mock = Mock()
    socket_mock.bind = Mock()
    socket_mock.sendto = Mock()
    socket_mock.recvfrom = Mock()
    socket_mock.close = Mock()
    socket_mock.setsockopt = Mock()
    return socket_mock


@pytest.fixture
def mock_tcp_socket():
    """Provide a mock TCP socket"""
    socket_mock = Mock()
    socket_mock.connect = Mock()
    socket_mock.send = Mock()
    socket_mock.recv = Mock()
    socket_mock.close = Mock()
    socket_mock.setsockopt = Mock()
    return socket_mock


# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def create_protocol_message_bytes() -> bytes:
        """Create valid protocol message bytes"""
        message = ScannerProtocolMessage(
            signature=ProtocolConstants.SIGNATURE,
            type_of_request=ProtocolConstants.TYPE_OF_REQUEST,
            initiator_ip=IPv4Address("192.168.1.100"),
            src_name=b"TestSrc",
            dst_name=b"TestDst"
        )
        return message.to_bytes()
    
    @staticmethod
    def create_invalid_protocol_bytes() -> bytes:
        """Create invalid protocol message bytes"""
        return b'\x00\x01\x02\x03' * 20  # Invalid signature and format
    
    @staticmethod
    def create_file_transfer_message_bytes() -> bytes:
        """Create valid file transfer message bytes"""
        message = ScannerProtocolMessage(
            signature=ProtocolConstants.SIGNATURE,
            type_of_request=ProtocolConstants.TYPE_OF_FILE_TRANSFER,
            initiator_ip=IPv4Address("192.168.1.100"),
            src_name=b"FileSender",
            dst_name=b"FileReceiver"
        )
        return message.to_bytes()


@pytest.fixture
def test_data_generator():
    """Provide test data generator"""
    return TestDataGenerator()


# Context managers for testing
@pytest.fixture
def mock_file_operations():
    """Mock file operations"""
    with patch('builtins.open', create=True) as mock_open, \
         patch('os.path.exists') as mock_exists, \
         patch('os.path.getsize') as mock_getsize:
        
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        mock_file = MagicMock()
        mock_file.read.return_value = b"test file content"
        mock_open.return_value.__enter__.return_value = mock_file
        
        yield {
            'open': mock_open,
            'exists': mock_exists,
            'getsize': mock_getsize,
            'file': mock_file
        }


@pytest.fixture
def mock_network_operations():
    """Mock network socket operations"""
    with patch('socket.socket') as mock_socket_class:
        mock_socket_instance = Mock()
        mock_socket_class.return_value = mock_socket_instance
        
        # Configure socket behavior
        mock_socket_instance.bind = Mock()
        mock_socket_instance.sendto = Mock()
        mock_socket_instance.recvfrom = Mock(return_value=(b"test_data", ("192.168.1.100", 706)))
        mock_socket_instance.close = Mock()
        mock_socket_instance.setsockopt = Mock()
        mock_socket_instance.settimeout = Mock()
        
        yield mock_socket_instance
