from typing import List, Tuple

import ipaddress
import netifaces
import socket
import time

from src.dto.network import ScannerProtocolMessage, ScannerProtocolMessageBuilder


# Configuration constants
UDP_PORT = 706
TCP_DST_PORT = 708


def get_default_interface_info() -> Tuple[str, str]:
    """Get local IP and broadcast IP from the default network interface"""
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
    
    print(f"Default interface: {interface_name}")
    print(f"Network: {network}")
    
    return local_ip, broadcast_ip


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
    # Get local IP and broadcast IP from default interface
    local_ip, broadcast_ip = get_default_interface_info()
    
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

