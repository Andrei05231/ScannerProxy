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
        # Get default gateway
        gateways = netifaces.gateways()
        default_gateway = gateways['default'][netifaces.AF_INET]
        interface_name = default_gateway[1]
        
        # Get interface addresses
        addrs = netifaces.ifaddresses(interface_name)
        addr_info = addrs[netifaces.AF_INET][0]
        local_ip = addr_info['addr']
        netmask = addr_info['netmask']
        
        # Calculate broadcast address
        network = ipaddress.IPv4Network(f'{local_ip}/{netmask}', strict=False)
        broadcast_ip = str(network.broadcast_address)
        
        return local_ip, broadcast_ip, interface_name
    
    @staticmethod
    def get_network_info(interface_name: str) -> ipaddress.IPv4Network:
        """Get network information for a specific interface."""
        addrs = netifaces.ifaddresses(interface_name)
        addr_info = addrs[netifaces.AF_INET][0]
        local_ip = addr_info['addr']
        netmask = addr_info['netmask']
        
        return ipaddress.IPv4Network(f'{local_ip}/{netmask}', strict=False)
    
    @staticmethod
    def list_available_interfaces() -> list[str]:
        """List all available network interfaces."""
        return netifaces.interfaces()
