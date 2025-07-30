"""
Unit tests for the ScannerService class.
Tests the main orchestration service that coordinates scanner operations.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from ipaddress import IPv4Address

from src.core.scanner_service import ScannerService
from src.dto.network_models import ScannerProtocolMessage, ProtocolConstants


class TestScannerService:
    """Test cases for ScannerService class"""
    
    def test_init(self):
        """Test ScannerService initialization"""
        service = ScannerService()
        
        assert service.logger is not None
        assert service.network_manager is not None
        assert service.local_ip == ""
        assert service.broadcast_ip == ""
        assert service.interface_name == ""
        assert service.discovery_service is None
        assert service.file_transfer_service is None
    
    @patch('src.core.scanner_service.NetworkInterfaceManager')
    @patch('src.core.scanner_service.AgentDiscoveryService')
    @patch('src.core.scanner_service.FileTransferService')
    def test_initialize_success(self, mock_file_transfer_class, mock_discovery_class, mock_network_manager_class, mock_config):
        """Test successful initialization"""
        # Setup mocks
        mock_network_manager = Mock()
        mock_network_manager.get_default_interface_info.return_value = ("192.168.1.100", "192.168.1.255", "eth0")
        mock_network_manager_class.return_value = mock_network_manager
        
        mock_discovery_service = Mock()
        mock_discovery_class.return_value = mock_discovery_service
        
        mock_file_transfer_service = Mock()
        mock_file_transfer_class.return_value = mock_file_transfer_service
        
        # Test initialization
        service = ScannerService()
        service.initialize()
        
        # Verify network information was set
        assert service.local_ip == "192.168.1.100"
        assert service.broadcast_ip == "192.168.1.255"
        assert service.interface_name == "eth0"
        
        # Verify services were initialized
        assert service.discovery_service == mock_discovery_service
        assert service.file_transfer_service == mock_file_transfer_service
        
        # Verify services were created with correct parameters
        mock_discovery_class.assert_called_once_with(
            local_ip="192.168.1.100",
            broadcast_ip="192.168.1.255",
            port=706
        )
        
        mock_file_transfer_class.assert_called_once_with(
            local_ip="192.168.1.100",
            port=706,
            tcp_port=708
        )
    
    @patch('src.core.scanner_service.NetworkInterfaceManager')
    def test_initialize_failure(self, mock_network_manager_class):
        """Test initialization failure"""
        # Setup mock to raise exception
        mock_network_manager = Mock()
        mock_network_manager.get_default_interface_info.side_effect = Exception("Network error")
        mock_network_manager_class.return_value = mock_network_manager
        
        service = ScannerService()
        
        with pytest.raises(Exception) as exc_info:
            service.initialize()
        
        assert "Network error" in str(exc_info.value)
    
    def test_discover_agents_not_initialized(self):
        """Test discover_agents when service is not initialized"""
        service = ScannerService()
        
        with pytest.raises(RuntimeError) as exc_info:
            service.discover_agents()
        
        assert "Scanner service not initialized" in str(exc_info.value)
    
    def test_discover_agents_success(self, mock_config, mock_discovered_agents):
        """Test successful agent discovery"""
        service = ScannerService()
        
        # Mock discovery service
        mock_discovery_service = Mock()
        mock_discovery_service.discover_agents.return_value = mock_discovered_agents
        service.discovery_service = mock_discovery_service
        
        # Test discovery
        result = service.discover_agents()
        
        # Verify result
        assert result == mock_discovered_agents
        assert len(result) == 2
        
        # Verify discovery service was called with correct parameters
        mock_discovery_service.discover_agents.assert_called_once_with(
            timeout=5.0,  # From mock_config
            src_name='TestScanner'  # From mock_config
        )
    
    def test_send_file_transfer_request_not_initialized(self):
        """Test file transfer request when service is not initialized"""
        service = ScannerService()
        
        success, response = service.send_file_transfer_request("192.168.1.100")
        
        assert success is False
        assert response is None
    
    def test_send_file_transfer_request_success_with_response(self, mock_config, sample_file_transfer_message):
        """Test successful file transfer request with response"""
        service = ScannerService()
        
        # Mock file transfer service
        mock_file_transfer_service = Mock()
        mock_file_transfer_service.send_file_transfer_request.return_value = (True, sample_file_transfer_message)
        service.file_transfer_service = mock_file_transfer_service
        
        # Test file transfer request
        success, response = service.send_file_transfer_request(
            target_ip="192.168.1.100",
            src_name="CustomSource",
            dst_name="CustomDestination",
            file_path="/custom/path/file.raw"
        )
        
        # Verify result
        assert success is True
        assert response == sample_file_transfer_message
        
        # Verify file transfer service was called correctly
        mock_file_transfer_service.send_file_transfer_request.assert_called_once_with(
            target_ip="192.168.1.100",
            src_name="CustomSource",
            dst_name="CustomDestination",
            file_path="/custom/path/file.raw",
            progress_callback=None
        )
    
    def test_send_file_transfer_request_success_no_response(self, mock_config):
        """Test successful file transfer request without response"""
        service = ScannerService()
        
        # Mock file transfer service
        mock_file_transfer_service = Mock()
        mock_file_transfer_service.send_file_transfer_request.return_value = (True, None)
        service.file_transfer_service = mock_file_transfer_service
        
        # Test file transfer request
        success, response = service.send_file_transfer_request("192.168.1.100")
        
        # Verify result
        assert success is True
        assert response is None
    
    def test_send_file_transfer_request_failure(self, mock_config):
        """Test failed file transfer request"""
        service = ScannerService()
        
        # Mock file transfer service
        mock_file_transfer_service = Mock()
        mock_file_transfer_service.send_file_transfer_request.return_value = (False, None)
        service.file_transfer_service = mock_file_transfer_service
        
        # Test file transfer request
        success, response = service.send_file_transfer_request("192.168.1.100")
        
        # Verify result
        assert success is False
        assert response is None
    
    def test_send_file_transfer_request_uses_config_defaults(self, mock_config):
        """Test that file transfer request uses config defaults when parameters are None"""
        service = ScannerService()
        
        # Mock file transfer service
        mock_file_transfer_service = Mock()
        mock_file_transfer_service.send_file_transfer_request.return_value = (True, None)
        service.file_transfer_service = mock_file_transfer_service
        
        # Test file transfer request with None parameters
        service.send_file_transfer_request(
            target_ip="192.168.1.100",
            src_name=None,
            file_path=None
        )
        
        # Verify config defaults were used
        mock_file_transfer_service.send_file_transfer_request.assert_called_once_with(
            target_ip="192.168.1.100",
            src_name="TestScanner",  # From mock_config
            dst_name="",
            file_path="test_scan.raw",  # From mock_config
            progress_callback=None
        )
    
    def test_send_file_transfer_request_with_progress_callback(self, mock_config):
        """Test file transfer request with progress callback"""
        service = ScannerService()
        
        # Mock file transfer service
        mock_file_transfer_service = Mock()
        mock_file_transfer_service.send_file_transfer_request.return_value = (True, None)
        service.file_transfer_service = mock_file_transfer_service
        
        # Mock progress callback
        mock_progress_callback = Mock()
        
        # Test file transfer request with progress callback
        service.send_file_transfer_request(
            target_ip="192.168.1.100",
            progress_callback=mock_progress_callback
        )
        
        # Verify progress callback was passed through
        mock_file_transfer_service.send_file_transfer_request.assert_called_once_with(
            target_ip="192.168.1.100",
            src_name="TestScanner",
            dst_name="",
            file_path="test_scan.raw",
            progress_callback=mock_progress_callback
        )
    
    def test_get_network_status_not_initialized(self):
        """Test get_network_status when service is not initialized"""
        service = ScannerService()
        
        status = service.get_network_status()
        
        expected = {
            "local_ip": "",
            "broadcast_ip": "",
            "interface_name": "",
            "is_initialized": False
        }
        
        assert status == expected
    
    def test_get_network_status_initialized(self):
        """Test get_network_status when service is initialized"""
        service = ScannerService()
        service.local_ip = "192.168.1.100"
        service.broadcast_ip = "192.168.1.255"
        service.interface_name = "eth0"
        service.discovery_service = Mock()  # Set to indicate initialization
        
        status = service.get_network_status()
        
        expected = {
            "local_ip": "192.168.1.100",
            "broadcast_ip": "192.168.1.255",
            "interface_name": "eth0",
            "is_initialized": True
        }
        
        assert status == expected
    
    @patch('src.core.scanner_service.NetworkInterfaceManager')
    def test_get_available_interfaces(self, mock_network_manager_class):
        """Test getting available network interfaces"""
        # Setup mock
        mock_network_manager = Mock()
        mock_network_manager.list_available_interfaces.return_value = ["eth0", "wlan0", "lo"]
        mock_network_manager_class.return_value = mock_network_manager
        
        service = ScannerService()
        
        interfaces = service.get_available_interfaces()
        
        assert interfaces == ["eth0", "wlan0", "lo"]
        mock_network_manager.list_available_interfaces.assert_called_once()


class TestScannerServiceIntegration:
    """Integration-style tests for ScannerService"""
    
    @patch('src.core.scanner_service.NetworkInterfaceManager')
    @patch('src.core.scanner_service.AgentDiscoveryService')
    @patch('src.core.scanner_service.FileTransferService')
    def test_full_workflow(self, mock_file_transfer_class, mock_discovery_class, mock_network_manager_class, mock_config, mock_discovered_agents, sample_file_transfer_message):
        """Test full workflow: initialize -> discover -> send file"""
        # Setup mocks
        mock_network_manager = Mock()
        mock_network_manager.get_default_interface_info.return_value = ("192.168.1.100", "192.168.1.255", "eth0")
        mock_network_manager_class.return_value = mock_network_manager
        
        mock_discovery_service = Mock()
        mock_discovery_service.discover_agents.return_value = mock_discovered_agents
        mock_discovery_class.return_value = mock_discovery_service
        
        mock_file_transfer_service = Mock()
        mock_file_transfer_service.send_file_transfer_request.return_value = (True, sample_file_transfer_message)
        mock_file_transfer_class.return_value = mock_file_transfer_service
        
        # Test full workflow
        service = ScannerService()
        
        # Step 1: Initialize
        service.initialize()
        assert service.local_ip == "192.168.1.100"
        
        # Step 2: Discover agents
        agents = service.discover_agents()
        assert len(agents) == 2
        
        # Step 3: Send file to discovered agent
        agent_message, agent_address = agents[0]
        target_ip = agent_address.split(':')[0]
        
        success, response = service.send_file_transfer_request(
            target_ip=target_ip,
            dst_name=agent_message.src_name.decode('ascii', errors='ignore')
        )
        
        assert success is True
        assert response == sample_file_transfer_message
        
        # Verify all services were called
        mock_discovery_service.discover_agents.assert_called_once()
        mock_file_transfer_service.send_file_transfer_request.assert_called_once()
