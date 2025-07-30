"""
Unit tests for the AgentDiscoveryService class.
Tests agent discovery functionality including UDP broadcast and response handling.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import socket
import threading
import time
from ipaddress import IPv4Address

from src.network.discovery import AgentDiscoveryService
from src.dto.network_models import ScannerProtocolMessage, ProtocolConstants


class TestAgentDiscoveryService:
    """Test cases for AgentDiscoveryService class"""
    
    def test_init(self):
        """Test AgentDiscoveryService initialization"""
        service = AgentDiscoveryService(
            local_ip="192.168.1.100",
            broadcast_ip="192.168.1.255",
            port=706
        )
        
        assert service.local_ip == "192.168.1.100"
        assert service.broadcast_ip == "192.168.1.255"
        assert service.port == 706
        assert service.logger is not None
    
    @patch('src.network.discovery.MessageBuilder')
    @patch('socket.socket')
    def test_discover_agents_success(self, mock_socket_class, mock_message_builder, sample_protocol_message):
        """Test successful agent discovery with responses"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock discovery message
        mock_discovery_msg = sample_protocol_message
        mock_message_builder.create_discovery_request.return_value = mock_discovery_msg
        
        # Mock agent responses
        agent1_response = ScannerProtocolMessage(
            src_name=b"Agent1",
            dst_name=b"Scanner",
            initiator_ip=IPv4Address("192.168.1.101")
        )
        agent2_response = ScannerProtocolMessage(
            src_name=b"Agent2", 
            dst_name=b"Scanner",
            initiator_ip=IPv4Address("192.168.1.102")
        )
        
        # Setup socket responses
        response_data = [
            (agent1_response.to_bytes(), ("192.168.1.101", 706)),
            (agent2_response.to_bytes(), ("192.168.1.102", 706))
        ]
        
        # Mock the receive loop to return responses then timeout
        mock_socket.recvfrom.side_effect = response_data + [socket.timeout("Discovery timeout")]
        
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        with patch('src.network.discovery.ScannerProtocolMessage.from_bytes') as mock_from_bytes:
            mock_from_bytes.side_effect = [agent1_response, agent2_response]
            
            # Test discovery
            agents = service.discover_agents(timeout=2.0, src_name="TestScanner")
        
        # Verify results
        assert len(agents) == 2
        assert agents[0][0] == agent1_response
        assert agents[0][1] == "192.168.1.101:706"
        assert agents[1][0] == agent2_response
        assert agents[1][1] == "192.168.1.102:706"
        
        # Verify socket operations
        mock_socket.bind.assert_called_once_with(("192.168.1.100", 706))
        mock_socket.sendto.assert_called_once()
        mock_socket.setsockopt.assert_called()
        mock_socket.close.assert_called_once()
        
        # Verify discovery message was created
        mock_message_builder.create_discovery_request.assert_called_once_with(
            initiator_ip="192.168.1.100",
            src_name="TestScanner"
        )
    
    @patch('src.network.discovery.MessageBuilder')
    @patch('socket.socket')
    def test_discover_agents_no_responses(self, mock_socket_class, mock_message_builder, sample_protocol_message):
        """Test agent discovery with no responses (timeout only)"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock discovery message
        mock_discovery_msg = sample_protocol_message
        mock_message_builder.create_discovery_request.return_value = mock_discovery_msg
        
        # Mock timeout immediately
        mock_socket.recvfrom.side_effect = socket.timeout("No agents found")
        
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        # Test discovery
        agents = service.discover_agents(timeout=1.0, src_name="TestScanner")
        
        # Verify no agents found
        assert len(agents) == 0
        
        # Verify socket operations
        mock_socket.bind.assert_called_once()
        mock_socket.sendto.assert_called_once()
        mock_socket.close.assert_called_once()
    
    @patch('src.network.discovery.MessageBuilder')
    @patch('socket.socket')
    def test_discover_agents_socket_error(self, mock_socket_class, mock_message_builder, sample_protocol_message):
        """Test agent discovery with socket error"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock discovery message
        mock_discovery_msg = sample_protocol_message
        mock_message_builder.create_discovery_request.return_value = mock_discovery_msg
        
        # Mock socket error during sendto
        mock_socket.sendto.side_effect = socket.error("Network unreachable")
        
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        # Test discovery should handle error gracefully
        agents = service.discover_agents(timeout=1.0, src_name="TestScanner")
        
        # Verify empty result due to error
        assert len(agents) == 0
        
        # Verify socket was closed
        mock_socket.close.assert_called_once()
    
    @patch('src.network.discovery.MessageBuilder')
    @patch('socket.socket')
    def test_discover_agents_invalid_response(self, mock_socket_class, mock_message_builder, sample_protocol_message):
        """Test agent discovery with invalid response data"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock discovery message
        mock_discovery_msg = sample_protocol_message
        mock_message_builder.create_discovery_request.return_value = mock_discovery_msg
        
        # Mock invalid response data
        invalid_data = b"invalid_message_data"
        mock_socket.recvfrom.side_effect = [
            (invalid_data, ("192.168.1.101", 706)),
            socket.timeout("Discovery timeout")
        ]
        
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        with patch('src.network.discovery.ScannerProtocolMessage.from_bytes') as mock_from_bytes:
            # Mock deserialization error
            mock_from_bytes.side_effect = Exception("Invalid message format")
            
            # Test discovery
            agents = service.discover_agents(timeout=1.0, src_name="TestScanner")
        
        # Verify invalid response was ignored
        assert len(agents) == 0
        
        # Verify socket operations completed
        mock_socket.close.assert_called_once()
    
    @patch('src.network.discovery.MessageBuilder')
    @patch('socket.socket')
    def test_discover_agents_mixed_responses(self, mock_socket_class, mock_message_builder, sample_protocol_message):
        """Test agent discovery with mix of valid and invalid responses"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock discovery message
        mock_discovery_msg = sample_protocol_message
        mock_message_builder.create_discovery_request.return_value = mock_discovery_msg
        
        # Create valid agent response
        valid_agent = ScannerProtocolMessage(
            src_name=b"ValidAgent",
            dst_name=b"Scanner",
            initiator_ip=IPv4Address("192.168.1.101")
        )
        
        # Setup mixed responses
        mock_socket.recvfrom.side_effect = [
            (b"invalid_data", ("192.168.1.100", 706)),  # Invalid response
            (valid_agent.to_bytes(), ("192.168.1.101", 706)),  # Valid response
            (b"more_invalid", ("192.168.1.102", 706)),  # Another invalid
            socket.timeout("Discovery timeout")
        ]
        
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        with patch('src.network.discovery.ScannerProtocolMessage.from_bytes') as mock_from_bytes:
            # Mock deserialization: error for invalid, success for valid
            mock_from_bytes.side_effect = [
                Exception("Invalid 1"),
                valid_agent,
                Exception("Invalid 2")
            ]
            
            # Test discovery
            agents = service.discover_agents(timeout=2.0, src_name="TestScanner")
        
        # Verify only valid agent was returned
        assert len(agents) == 1
        assert agents[0][0] == valid_agent
        assert agents[0][1] == "192.168.1.101:706"
    
    @patch('src.network.discovery.MessageBuilder')
    @patch('socket.socket')
    def test_discover_agents_duplicate_responses(self, mock_socket_class, mock_message_builder, sample_protocol_message):
        """Test agent discovery with duplicate responses from same agent"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock discovery message
        mock_discovery_msg = sample_protocol_message
        mock_message_builder.create_discovery_request.return_value = mock_discovery_msg
        
        # Create agent response
        agent_response = ScannerProtocolMessage(
            src_name=b"Agent1",
            dst_name=b"Scanner",
            initiator_ip=IPv4Address("192.168.1.101")
        )
        
        # Setup duplicate responses from same address
        mock_socket.recvfrom.side_effect = [
            (agent_response.to_bytes(), ("192.168.1.101", 706)),
            (agent_response.to_bytes(), ("192.168.1.101", 706)),  # Duplicate
            socket.timeout("Discovery timeout")
        ]
        
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        with patch('src.network.discovery.ScannerProtocolMessage.from_bytes') as mock_from_bytes:
            mock_from_bytes.return_value = agent_response
            
            # Test discovery
            agents = service.discover_agents(timeout=1.0, src_name="TestScanner")
        
        # Verify duplicate was handled (implementation detail - may keep both or dedupe)
        # This test verifies the service handles duplicates gracefully
        assert len(agents) >= 1  # At least one response
        
        # Verify all responses are from expected agent
        for agent, address in agents:
            assert agent.src_name == b"Agent1"
            assert address == "192.168.1.101:706"
    
    def test_discover_agents_zero_timeout(self):
        """Test agent discovery with zero timeout"""
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        with patch('socket.socket') as mock_socket_class:
            mock_socket = Mock()
            mock_socket_class.return_value = mock_socket
            mock_socket.recvfrom.side_effect = socket.timeout("Immediate timeout")
            
            with patch('src.network.discovery.MessageBuilder') as mock_message_builder:
                mock_message_builder.create_discovery_request.return_value = ScannerProtocolMessage()
                
                # Test with zero timeout
                agents = service.discover_agents(timeout=0.0, src_name="TestScanner")
        
        # Should complete quickly with no agents
        assert len(agents) == 0
    
    def test_discover_agents_negative_timeout(self):
        """Test agent discovery with negative timeout"""
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        with patch('socket.socket') as mock_socket_class:
            mock_socket = Mock()
            mock_socket_class.return_value = mock_socket
            mock_socket.recvfrom.side_effect = socket.timeout("Immediate timeout")
            
            with patch('src.network.discovery.MessageBuilder') as mock_message_builder:
                mock_message_builder.create_discovery_request.return_value = ScannerProtocolMessage()
                
                # Test with negative timeout (should be handled gracefully)
                agents = service.discover_agents(timeout=-1.0, src_name="TestScanner")
        
        # Should complete with no agents
        assert len(agents) == 0
    
    @patch('src.network.discovery.MessageBuilder')
    @patch('socket.socket')
    def test_discover_agents_long_timeout(self, mock_socket_class, mock_message_builder, sample_protocol_message):
        """Test agent discovery with long timeout but early completion"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock discovery message
        mock_discovery_msg = sample_protocol_message
        mock_message_builder.create_discovery_request.return_value = mock_discovery_msg
        
        # Mock immediate timeout (simulating no agents)
        mock_socket.recvfrom.side_effect = socket.timeout("No responses")
        
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        # Start time measurement
        start_time = time.time()
        
        # Test with long timeout
        agents = service.discover_agents(timeout=30.0, src_name="TestScanner")
        
        # Verify it completed quickly (within 5 seconds, not 30)
        elapsed_time = time.time() - start_time
        assert elapsed_time < 5.0
        assert len(agents) == 0
    
    @patch('src.network.discovery.MessageBuilder')
    @patch('socket.socket') 
    def test_discover_agents_custom_src_name(self, mock_socket_class, mock_message_builder, sample_protocol_message):
        """Test agent discovery with custom source name"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock discovery message
        mock_discovery_msg = sample_protocol_message
        mock_message_builder.create_discovery_request.return_value = mock_discovery_msg
        
        # Mock timeout (no responses needed for this test)
        mock_socket.recvfrom.side_effect = socket.timeout("No responses")
        
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        # Test with custom source name
        custom_src_name = "CustomScannerName"
        agents = service.discover_agents(timeout=1.0, src_name=custom_src_name)
        
        # Verify custom source name was used
        mock_message_builder.create_discovery_request.assert_called_once_with(
            initiator_ip="192.168.1.100",
            src_name=custom_src_name
        )
        
        assert len(agents) == 0  # No responses expected


class TestAgentDiscoveryServiceEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_init_with_invalid_ips(self):
        """Test initialization with invalid IP addresses"""
        # Should not raise during initialization (validation happens during use)
        service = AgentDiscoveryService(
            local_ip="invalid.ip",
            broadcast_ip="another.invalid",
            port=706
        )
        
        assert service.local_ip == "invalid.ip"
        assert service.broadcast_ip == "another.invalid"
        assert service.port == 706
    
    def test_init_with_invalid_port(self):
        """Test initialization with invalid port numbers"""
        # Test with port 0
        service1 = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 0)
        assert service1.port == 0
        
        # Test with very high port
        service2 = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 99999)
        assert service2.port == 99999
        
        # Test with negative port
        service3 = AgentDiscoveryService("192.168.1.100", "192.168.1.255", -1)
        assert service3.port == -1
    
    @patch('src.network.discovery.MessageBuilder')
    @patch('socket.socket')
    def test_discover_agents_bind_error(self, mock_socket_class, mock_message_builder, sample_protocol_message):
        """Test agent discovery with socket bind error"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock bind error
        mock_socket.bind.side_effect = socket.error("Address already in use")
        
        # Mock discovery message
        mock_discovery_msg = sample_protocol_message
        mock_message_builder.create_discovery_request.return_value = mock_discovery_msg
        
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        # Test discovery with bind error
        agents = service.discover_agents(timeout=1.0, src_name="TestScanner")
        
        # Should handle error gracefully
        assert len(agents) == 0
        
        # Verify socket was closed
        mock_socket.close.assert_called_once()
    
    @patch('src.network.discovery.MessageBuilder')
    @patch('socket.socket')
    def test_discover_agents_settimeout_error(self, mock_socket_class, mock_message_builder, sample_protocol_message):
        """Test agent discovery with settimeout error"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock settimeout error
        mock_socket.settimeout.side_effect = socket.error("Invalid timeout")
        
        # Mock discovery message
        mock_discovery_msg = sample_protocol_message
        mock_message_builder.create_discovery_request.return_value = mock_discovery_msg
        
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        # Test discovery with settimeout error
        agents = service.discover_agents(timeout=1.0, src_name="TestScanner")
        
        # Should handle error gracefully
        assert len(agents) == 0
        
        # Verify socket was closed
        mock_socket.close.assert_called_once()


class TestAgentDiscoveryServiceIntegration:
    """Integration-style tests for AgentDiscoveryService"""
    
    @patch('src.network.discovery.MessageBuilder')
    @patch('socket.socket')
    def test_realistic_discovery_scenario(self, mock_socket_class, mock_message_builder, sample_protocol_message):
        """Test realistic discovery scenario with multiple agents and timing"""
        # Setup mocks
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock discovery message
        mock_discovery_msg = sample_protocol_message
        mock_message_builder.create_discovery_request.return_value = mock_discovery_msg
        
        # Create realistic agent responses
        agents_data = [
            ("PrintServer1", "192.168.1.10"),
            ("Scanner_Device", "192.168.1.15"),
            ("NetworkPrinter", "192.168.1.20")
        ]
        
        agent_responses = []
        for name, ip in agents_data:
            agent = ScannerProtocolMessage(
                src_name=name.encode('ascii')[:20].ljust(20, b'\x00'),
                dst_name=b"Scanner".ljust(40, b'\x00'),
                initiator_ip=IPv4Address(ip)
            )
            agent_responses.append(agent)
        
        # Setup socket responses with realistic timing
        socket_responses = []
        for i, agent in enumerate(agent_responses):
            socket_responses.append((agent.to_bytes(), (agents_data[i][1], 706)))
        
        socket_responses.append(socket.timeout("Discovery complete"))
        mock_socket.recvfrom.side_effect = socket_responses
        
        service = AgentDiscoveryService("192.168.1.100", "192.168.1.255", 706)
        
        with patch('src.network.discovery.ScannerProtocolMessage.from_bytes') as mock_from_bytes:
            mock_from_bytes.side_effect = agent_responses
            
            # Test realistic discovery
            discovered_agents = service.discover_agents(timeout=5.0, src_name="MainScanner")
        
        # Verify all agents were discovered
        assert len(discovered_agents) == 3
        
        # Verify agent details
        for i, (agent_msg, address) in enumerate(discovered_agents):
            expected_name, expected_ip = agents_data[i]
            assert agent_msg.src_name.decode('ascii', errors='ignore').strip('\x00') == expected_name
            assert address == f"{expected_ip}:706"
        
        # Verify socket operations
        mock_socket.bind.assert_called_once_with(("192.168.1.100", 706))
        mock_socket.sendto.assert_called_once()
        mock_socket.close.assert_called_once()
