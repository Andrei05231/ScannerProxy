from typing import List, Tuple, Optional

import ipaddress
import netifaces
import socket
import time

from src.dto.network import ScannerProtocolMessage, ScannerProtocolMessageBuilder


UDP_PORT = 706
TCP_DST_PORT = 708


def get_local_ip() -> str:
    """Get the local IP address dynamically"""
    try:
        # Create a socket and connect to a remote address (doesn't actually send data)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def get_network_info(ip_address: str) -> Optional[ipaddress.IPv4Network]:
    """Get network information for the given IP address using netifaces"""

    try:
        # Get all network interfaces
        interfaces = netifaces.interfaces()
        
        for interface in interfaces:
            # Get IPv4 addresses for this interface
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr_info in addrs[netifaces.AF_INET]:
                    if addr_info.get('addr') == ip_address:
                        # Found the interface with our IP
                        netmask = addr_info.get('netmask')
                        if netmask:
                            # Create network from IP and netmask
                            network = ipaddress.IPv4Network(f'{ip_address}/{netmask}', strict=False)
                            return network
                            
    except Exception as e:
        print(f"Warning: Could not get network info using netifaces: {e}")
    
    # Fallback to /24 if we can't determine the subnet
    try:
        return ipaddress.IPv4Network(f'{ip_address}/24', strict=False)
    except:
        return None


def get_broadcast_ip(local_ip: str) -> str:
    """Generate broadcast IP from local IP using network detection"""
    network_info = get_network_info(local_ip)
    
    if network_info:
        broadcast_ip = str(network_info.broadcast_address)
        print(f"Detected network: {network_info} (broadcast: {broadcast_ip})")
        return broadcast_ip
    else:
        # Final fallback to /24 assumption
        ip_parts = local_ip.split('.')
        fallback_broadcast = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.255"
        print(f"Warning: Could not detect network, assuming /24. Using broadcast: {fallback_broadcast}")
        return fallback_broadcast

def discover_agents(local_ip: str, broadcast_ip: str, port: int, timeout: float = 5.0) -> List[Tuple[ScannerProtocolMessage, str]]:
    """
    Discover agents on the network that are listening for scanned documents
    Returns a list of tuples containing (response_message, sender_address)
    """
    responses = []
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting
    sock.settimeout(1.0)  # Short timeout for individual receives
    sock.bind((local_ip, port))

    try:
        # Build discovery message using the builder pattern
        builder = ScannerProtocolMessageBuilder()
        discovery_message = builder.build_discovery_message(local_ip, "Test-name")
        
        print("=== DISCOVERY MESSAGE ===")
        discovery_message.debug()
        print()
        
        # Send broadcast message
        udp_packet_bytes = discovery_message.to_bytes()
        print(f"Sending discovery packet ({len(udp_packet_bytes)} bytes) to {broadcast_ip}:{port}...")
        sock.sendto(udp_packet_bytes, (broadcast_ip, port))
        
        # Listen for responses for the specified timeout period
        start_time = time.time()
        response_count = 0
        
        print(f"Listening for responses for {timeout} seconds...")
        print()
        
        while time.time() - start_time < timeout:
            try:
                resp, addr = sock.recvfrom(1024)
                response_count += 1
                
                print(f"=== RESPONSE #{response_count} FROM {addr[0]}:{addr[1]} ===")
                try:
                    response_message = ScannerProtocolMessage.from_bytes(resp)
                    response_message.debug()
                    responses.append((response_message, f"{addr[0]}:{addr[1]}"))
                    print(f"Successfully parsed response from {addr}")
                except Exception as e:
                    print(f"Failed to parse response from {addr}: {e}")
                    print(f"Raw response: {resp.hex()}")
                
                print()
                
            except socket.timeout:
                # Continue listening until overall timeout
                continue
                
    except Exception as e:
        print(f"Error during discovery: {e}")
    finally:
        sock.close()
    
    return responses


if __name__ == "__main__":
    # Get local IP dynamically
    local_ip = get_local_ip()
    broadcast_ip = get_broadcast_ip(local_ip)
    
    print(f"Local IP: {local_ip}")
    print(f"Broadcast IP: {broadcast_ip}")
    print("Starting agent discovery...")
    print()
    
    # Discover agents on the network that are listening for scanned documents
    discovered_agents = discover_agents(local_ip, broadcast_ip, UDP_PORT, timeout=10.0)
    
    print("=== DISCOVERY SUMMARY ===")
    if discovered_agents:
        print(f"Found {len(discovered_agents)} agent(s) listening for scanned documents:")
        for i, (message, address) in enumerate(discovered_agents, 1):
            print(f"{i}. Agent at {address}")
            print(f"   Source Name: {message.src_name.decode('ascii', errors='ignore')}")
            print(f"   Destination Name: {message.dst_name.decode('ascii', errors='ignore')}")
            print(f"   IP: {message.initiator_ip}")
    else:
        print("No agents discovered on the network listening for scanned documents.")

