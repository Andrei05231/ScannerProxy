"""
Unit tests for the NetworkInterfaceManager class.
Tests network interface detection and management functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import netifaces
import socket

from src.network.interfaces import NetworkInterfaceManager


class TestNetworkInterfaceManager:
    """Test cases for NetworkInterfaceManager class"""
    
    def test_init(self):
        """Test NetworkInterfaceManager initialization"""
        manager = NetworkInterfaceManager()
        assert manager.logger is not None
    
    @patch('src.network.interfaces.netifaces.interfaces')
    def test_list_available_interfaces(self, mock_interfaces):
        """Test listing available network interfaces"""
        # Mock available interfaces
        mock_interfaces.return_value = ['lo', 'eth0', 'wlan0', 'docker0']
        
        manager = NetworkInterfaceManager()
        interfaces = manager.list_available_interfaces()
        
        assert interfaces == ['lo', 'eth0', 'wlan0', 'docker0']
        mock_interfaces.assert_called_once()
    
    @patch('src.network.interfaces.netifaces.interfaces')
    def test_list_available_interfaces_empty(self, mock_interfaces):
        """Test listing interfaces when none are available"""
        # Mock no interfaces
        mock_interfaces.return_value = []
        
        manager = NetworkInterfaceManager()
        interfaces = manager.list_available_interfaces()
        
        assert interfaces == []
        mock_interfaces.assert_called_once()
    
    @patch('src.network.interfaces.netifaces.interfaces')
    def test_list_available_interfaces_error(self, mock_interfaces):
        """Test listing interfaces with error"""
        # Mock netifaces error
        mock_interfaces.side_effect = Exception("Network interfaces unavailable")
        
        manager = NetworkInterfaceManager()
        interfaces = manager.list_available_interfaces()
        
        # Should return empty list on error
        assert interfaces == []
        mock_interfaces.assert_called_once()
    
    @patch('src.network.interfaces.netifaces.ifaddresses')
    @patch('src.network.interfaces.netifaces.interfaces')
    def test_get_interface_info_success(self, mock_interfaces, mock_ifaddresses):
        """Test getting interface information successfully"""
        # Mock interface addresses
        mock_ifaddresses.return_value = {
            netifaces.AF_INET: [
                {
                    'addr': '192.168.1.100',
                    'netmask': '255.255.255.0',
                    'broadcast': '192.168.1.255'
                }
            ]
        }
        
        manager = NetworkInterfaceManager()
        local_ip, broadcast_ip = manager.get_interface_info('eth0')
        
        assert local_ip == '192.168.1.100'
        assert broadcast_ip == '192.168.1.255'
        mock_ifaddresses.assert_called_once_with('eth0')
    
    @patch('src.network.interfaces.netifaces.ifaddresses')
    def test_get_interface_info_no_ipv4(self, mock_ifaddresses):
        """Test getting interface info when no IPv4 address exists"""
        # Mock interface with no IPv4 addresses
        mock_ifaddresses.return_value = {
            netifaces.AF_LINK: [{'addr': '00:11:22:33:44:55'}]
        }
        
        manager = NetworkInterfaceManager()
        
        with pytest.raises(ValueError) as exc_info:
            manager.get_interface_info('eth0')
        
        assert "No IPv4 address found" in str(exc_info.value)
        mock_ifaddresses.assert_called_once_with('eth0')
    
    @patch('src.network.interfaces.netifaces.ifaddresses')
    def test_get_interface_info_empty_addresses(self, mock_ifaddresses):
        """Test getting interface info with empty IPv4 addresses"""
        # Mock interface with empty IPv4 list
        mock_ifaddresses.return_value = {
            netifaces.AF_INET: []
        }
        
        manager = NetworkInterfaceManager()
        
        with pytest.raises(ValueError) as exc_info:
            manager.get_interface_info('eth0')
        
        assert "No IPv4 address found" in str(exc_info.value)
        mock_ifaddresses.assert_called_once_with('eth0')
    
    @patch('src.network.interfaces.netifaces.ifaddresses')
    def test_get_interface_info_missing_broadcast(self, mock_ifaddresses):
        """Test getting interface info when broadcast address is missing"""
        # Mock interface with IP but no broadcast
        mock_ifaddresses.return_value = {
            netifaces.AF_INET: [
                {
                    'addr': '192.168.1.100',
                    'netmask': '255.255.255.0'
                    # Missing 'broadcast' key
                }
            ]
        }
        
        manager = NetworkInterfaceManager()
        local_ip, broadcast_ip = manager.get_interface_info('eth0')
        
        assert local_ip == '192.168.1.100'
        assert broadcast_ip == '192.168.1.255'  # Should be calculated
        mock_ifaddresses.assert_called_once_with('eth0')
    
    @patch('src.network.interfaces.netifaces.ifaddresses')
    def test_get_interface_info_error(self, mock_ifaddresses):
        """Test getting interface info with netifaces error"""
        # Mock netifaces error
        mock_ifaddresses.side_effect = Exception("Interface not found")
        
        manager = NetworkInterfaceManager()
        
        with pytest.raises(Exception) as exc_info:
            manager.get_interface_info('nonexistent')
        
        assert "Interface not found" in str(exc_info.value)
        mock_ifaddresses.assert_called_once_with('nonexistent')
    
    @patch('src.network.interfaces.netifaces.ifaddresses')
    @patch('src.network.interfaces.netifaces.interfaces')
    def test_get_default_interface_info_success(self, mock_interfaces, mock_ifaddresses):
        """Test getting default interface info successfully"""
        # Mock available interfaces
        mock_interfaces.return_value = ['lo', 'eth0', 'wlan0']
        
        # Mock interface addresses for eth0 (first non-loopback)
        mock_ifaddresses.return_value = {
            netifaces.AF_INET: [
                {
                    'addr': '192.168.1.100',
                    'netmask': '255.255.255.0',
                    'broadcast': '192.168.1.255'
                }
            ]
        }
        
        manager = NetworkInterfaceManager()
        local_ip, broadcast_ip, interface_name = manager.get_default_interface_info()
        
        assert local_ip == '192.168.1.100'
        assert broadcast_ip == '192.168.1.255'
        assert interface_name == 'eth0'
        
        # Should check eth0 first (skip loopback)
        mock_ifaddresses.assert_called_with('eth0')
    
    @patch('src.network.interfaces.netifaces.ifaddresses')
    @patch('src.network.interfaces.netifaces.interfaces')
    def test_get_default_interface_info_skip_loopback(self, mock_interfaces, mock_ifaddresses):
        """Test that loopback interface is skipped"""
        # Mock interfaces with loopback first
        mock_interfaces.return_value = ['lo', 'eth0']
        
        # Mock loopback address (should be skipped)
        def mock_ifaddresses_func(interface):
            if interface == 'lo':
                return {
                    netifaces.AF_INET: [
                        {
                            'addr': '127.0.0.1',
                            'netmask': '255.0.0.0',
                            'broadcast': '127.255.255.255'
                        }
                    ]
                }
            elif interface == 'eth0':
                return {
                    netifaces.AF_INET: [
                        {
                            'addr': '192.168.1.100',
                            'netmask': '255.255.255.0',
                            'broadcast': '192.168.1.255'
                        }
                    ]
                }
        
        mock_ifaddresses.side_effect = mock_ifaddresses_func
        
        manager = NetworkInterfaceManager()
        local_ip, broadcast_ip, interface_name = manager.get_default_interface_info()
        
        assert local_ip == '192.168.1.100'
        assert broadcast_ip == '192.168.1.255'
        assert interface_name == 'eth0'
        
        # Should have checked both interfaces but returned eth0
        assert mock_ifaddresses.call_count >= 1
    
    @patch('src.network.interfaces.netifaces.ifaddresses')
    @patch('src.network.interfaces.netifaces.interfaces')
    def test_get_default_interface_info_no_valid_interfaces(self, mock_interfaces, mock_ifaddresses):
        """Test getting default interface when no valid interfaces exist"""
        # Mock only loopback interface
        mock_interfaces.return_value = ['lo']
        
        # Mock loopback address
        mock_ifaddresses.return_value = {
            netifaces.AF_INET: [
                {
                    'addr': '127.0.0.1',
                    'netmask': '255.0.0.0'
                }
            ]
        }
        
        manager = NetworkInterfaceManager()
        
        with pytest.raises(RuntimeError) as exc_info:
            manager.get_default_interface_info()
        
        assert "No suitable network interface found" in str(exc_info.value)
    
    @patch('src.network.interfaces.netifaces.ifaddresses')
    @patch('src.network.interfaces.netifaces.interfaces')
    def test_get_default_interface_info_all_interfaces_fail(self, mock_interfaces, mock_ifaddresses):
        """Test getting default interface when all interfaces fail"""
        # Mock available interfaces
        mock_interfaces.return_value = ['eth0', 'wlan0']
        
        # Mock all interfaces failing
        mock_ifaddresses.side_effect = Exception("Interface error")
        
        manager = NetworkInterfaceManager()
        
        with pytest.raises(RuntimeError) as exc_info:
            manager.get_default_interface_info()
        
        assert "No suitable network interface found" in str(exc_info.value)
    
    @patch('src.network.interfaces.netifaces.interfaces')
    def test_get_default_interface_info_no_interfaces(self, mock_interfaces):
        """Test getting default interface when no interfaces are available"""
        # Mock no interfaces
        mock_interfaces.return_value = []
        
        manager = NetworkInterfaceManager()
        
        with pytest.raises(RuntimeError) as exc_info:
            manager.get_default_interface_info()
        
        assert "No suitable network interface found" in str(exc_info.value)
    
    def test_is_loopback_interface_true(self):
        """Test loopback interface detection - positive cases"""
        manager = NetworkInterfaceManager()
        
        assert manager._is_loopback_interface('lo') is True
        assert manager._is_loopback_interface('lo0') is True
        assert manager._is_loopback_interface('Loopback') is True
        assert manager._is_loopback_interface('LOOPBACK') is True
    
    def test_is_loopback_interface_false(self):
        """Test loopback interface detection - negative cases"""
        manager = NetworkInterfaceManager()
        
        assert manager._is_loopback_interface('eth0') is False
        assert manager._is_loopback_interface('wlan0') is False
        assert manager._is_loopback_interface('docker0') is False
        assert manager._is_loopback_interface('br0') is False
        assert manager._is_loopback_interface('enp0s3') is False
    
    def test_is_loopback_interface_empty(self):
        """Test loopback interface detection with empty/None values"""
        manager = NetworkInterfaceManager()
        
        assert manager._is_loopback_interface('') is False
        assert manager._is_loopback_interface(None) is False
    
    def test_calculate_broadcast_address(self):
        """Test broadcast address calculation"""
        manager = NetworkInterfaceManager()
        
        # Test standard /24 network
        result = manager._calculate_broadcast_address('192.168.1.100', '255.255.255.0')
        assert result == '192.168.1.255'
        
        # Test /16 network
        result = manager._calculate_broadcast_address('10.0.5.100', '255.255.0.0')
        assert result == '10.0.255.255'
        
        # Test /8 network
        result = manager._calculate_broadcast_address('10.5.10.100', '255.0.0.0')
        assert result == '10.255.255.255'
        
        # Test /30 network (small subnet)
        result = manager._calculate_broadcast_address('192.168.1.1', '255.255.255.252')
        assert result == '192.168.1.3'
    
    def test_calculate_broadcast_address_invalid_ip(self):
        """Test broadcast calculation with invalid IP"""
        manager = NetworkInterfaceManager()
        
        with pytest.raises(Exception):
            manager._calculate_broadcast_address('invalid.ip', '255.255.255.0')
    
    def test_calculate_broadcast_address_invalid_netmask(self):
        """Test broadcast calculation with invalid netmask"""
        manager = NetworkInterfaceManager()
        
        with pytest.raises(Exception):
            manager._calculate_broadcast_address('192.168.1.100', 'invalid.mask')


class TestNetworkInterfaceManagerIntegration:
    """Integration-style tests for NetworkInterfaceManager"""
    
    @patch('src.network.interfaces.netifaces.ifaddresses')
    @patch('src.network.interfaces.netifaces.interfaces')
    def test_realistic_network_scenario(self, mock_interfaces, mock_ifaddresses):
        """Test realistic network scenario with multiple interfaces"""
        # Mock realistic interface list
        mock_interfaces.return_value = ['lo', 'eth0', 'wlan0', 'docker0', 'br-123456']
        
        # Mock interface configurations
        def mock_ifaddresses_func(interface):
            interface_configs = {
                'lo': {
                    netifaces.AF_INET: [
                        {
                            'addr': '127.0.0.1',
                            'netmask': '255.0.0.0'
                        }
                    ]
                },
                'eth0': {
                    netifaces.AF_INET: [
                        {
                            'addr': '192.168.1.100',
                            'netmask': '255.255.255.0',
                            'broadcast': '192.168.1.255'
                        }
                    ]
                },
                'wlan0': {
                    netifaces.AF_INET: [
                        {
                            'addr': '10.0.0.50',
                            'netmask': '255.255.255.0',
                            'broadcast': '10.0.0.255'
                        }
                    ]
                },
                'docker0': {
                    netifaces.AF_INET: [
                        {
                            'addr': '172.17.0.1',
                            'netmask': '255.255.0.0',
                            'broadcast': '172.17.255.255'
                        }
                    ]
                },
                'br-123456': {
                    netifaces.AF_LINK: [
                        {'addr': '02:42:ac:11:00:01'}
                    ]
                    # No IPv4 address
                }
            }
            return interface_configs.get(interface, {})
        
        mock_ifaddresses.side_effect = mock_ifaddresses_func
        
        manager = NetworkInterfaceManager()
        
        # Test listing all interfaces
        interfaces = manager.list_available_interfaces()
        assert len(interfaces) == 5
        assert 'eth0' in interfaces
        assert 'wlan0' in interfaces
        
        # Test getting specific interface info
        local_ip, broadcast_ip = manager.get_interface_info('eth0')
        assert local_ip == '192.168.1.100'
        assert broadcast_ip == '192.168.1.255'
        
        # Test getting default interface (should prefer eth0 over wlan0)
        local_ip, broadcast_ip, interface_name = manager.get_default_interface_info()
        assert interface_name == 'eth0'  # First non-loopback with IPv4
        assert local_ip == '192.168.1.100'
        assert broadcast_ip == '192.168.1.255'
    
    @patch('src.network.interfaces.netifaces.ifaddresses')
    @patch('src.network.interfaces.netifaces.interfaces')
    def test_wireless_only_scenario(self, mock_interfaces, mock_ifaddresses):
        """Test scenario with only wireless interface available"""
        # Mock only wireless interface (plus loopback)
        mock_interfaces.return_value = ['lo', 'wlan0']
        
        def mock_ifaddresses_func(interface):
            if interface == 'lo':
                return {
                    netifaces.AF_INET: [
                        {
                            'addr': '127.0.0.1',
                            'netmask': '255.0.0.0'
                        }
                    ]
                }
            elif interface == 'wlan0':
                return {
                    netifaces.AF_INET: [
                        {
                            'addr': '192.168.0.105',
                            'netmask': '255.255.255.0'
                            # No explicit broadcast - should be calculated
                        }
                    ]
                }
        
        mock_ifaddresses.side_effect = mock_ifaddresses_func
        
        manager = NetworkInterfaceManager()
        
        # Should use wireless interface as default
        local_ip, broadcast_ip, interface_name = manager.get_default_interface_info()
        assert interface_name == 'wlan0'
        assert local_ip == '192.168.0.105'
        assert broadcast_ip == '192.168.0.255'  # Calculated
    
    @patch('src.network.interfaces.netifaces.ifaddresses')
    @patch('src.network.interfaces.netifaces.interfaces')
    def test_docker_environment_scenario(self, mock_interfaces, mock_ifaddresses):
        """Test scenario in Docker environment with bridge networks"""
        # Mock Docker-like interface setup
        mock_interfaces.return_value = ['lo', 'eth0', 'docker0', 'br-abcd1234']
        
        def mock_ifaddresses_func(interface):
            configs = {
                'lo': {
                    netifaces.AF_INET: [{'addr': '127.0.0.1', 'netmask': '255.0.0.0'}]
                },
                'eth0': {
                    netifaces.AF_INET: [
                        {
                            'addr': '172.18.0.5',
                            'netmask': '255.255.0.0',
                            'broadcast': '172.18.255.255'
                        }
                    ]
                },
                'docker0': {
                    netifaces.AF_INET: [
                        {
                            'addr': '172.17.0.1',
                            'netmask': '255.255.0.0',
                            'broadcast': '172.17.255.255'
                        }
                    ]
                },
                'br-abcd1234': {
                    netifaces.AF_INET: [
                        {
                            'addr': '172.19.0.1',
                            'netmask': '255.255.0.0',
                            'broadcast': '172.19.255.255'
                        }
                    ]
                }
            }
            return configs.get(interface, {})
        
        mock_ifaddresses.side_effect = mock_ifaddresses_func
        
        manager = NetworkInterfaceManager()
        
        # Should prefer eth0 as the main interface
        local_ip, broadcast_ip, interface_name = manager.get_default_interface_info()
        assert interface_name == 'eth0'
        assert local_ip == '172.18.0.5'
        assert broadcast_ip == '172.18.255.255'
