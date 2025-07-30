"""
Agent discovery service.
Follows SRP - Single responsibility for network discovery operations.
"""
from typing import List, Tuple
import socket
import time

from ..dto.network_models import ScannerProtocolMessage
from ..network.protocols.message_builder import ScannerProtocolMessageBuilder


class AgentDiscoveryService:
    """Service for discovering agents on the network."""
    
    def __init__(self, local_ip: str, broadcast_ip: str, port: int):
        self.local_ip = local_ip
        self.broadcast_ip = broadcast_ip
        self.port = port
    
    def discover_agents(self, timeout: float = 10.0, src_name: str = "Scanner") -> List[Tuple[ScannerProtocolMessage, str]]:
        """
        Discover agents on the network that are listening for scanned documents.
        
        Args:
            timeout: How long to listen for responses
            src_name: Source name to include in the discovery message
            
        Returns:
            List of tuples containing (response_message, sender_address)
        """
        responses = []
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1.0)
        sock.bind((self.local_ip, self.port))

        try:
            # Build and send discovery message
            discovery_message = self._build_discovery_message(src_name)
            udp_packet_bytes = discovery_message.to_bytes()
            
            print(f"Sending discovery packet ({len(udp_packet_bytes)} bytes) to {self.broadcast_ip}:{self.port}...")
            sock.sendto(udp_packet_bytes, (self.broadcast_ip, self.port))
            
            # Listen for responses
            responses = self._listen_for_responses(sock, timeout)
            
        except Exception as e:
            print(f"Error during discovery: {e}")
        finally:
            sock.close()
        
        return responses
    
    def _build_discovery_message(self, src_name: str) -> ScannerProtocolMessage:
        """Build a discovery message using the builder pattern."""
        builder = ScannerProtocolMessageBuilder()
        return builder.build_discovery_message(self.local_ip, src_name)
    
    def _listen_for_responses(self, sock: socket.socket, timeout: float) -> List[Tuple[ScannerProtocolMessage, str]]:
        """Listen for agent responses."""
        responses = []
        start_time = time.time()
        response_count = 0
        
        print(f"Listening for responses for {timeout} seconds...")
        
        while time.time() - start_time < timeout:
            try:
                resp, addr = sock.recvfrom(1024)
                response_count += 1
                
                print(f"=== RESPONSE #{response_count} FROM {addr[0]}:{addr[1]} ===")
                try:
                    response_message = ScannerProtocolMessage.from_bytes(resp)
                    responses.append((response_message, f"{addr[0]}:{addr[1]}"))
                    print(f"Successfully parsed response from {addr}")
                except Exception as e:
                    print(f"Failed to parse response from {addr}: {e}")
                    print(f"Raw response: {resp.hex()}")
                
            except socket.timeout:
                continue
                
        return responses
