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


class FileTransferService:
    """
    Handles file transfer operations - SRP: Single responsibility for file transfer
    Follows the same pattern as AgentDiscoveryService for code reusability
    """
    
    def __init__(self, local_ip: str, port: int = 706):
        """
        Initialize file transfer service
        
        Args:
            local_ip: Local IP address for sending
            port: Port number for communication (default: 706)
        """
        self.local_ip = local_ip
        self.port = port
        self.logger = logging.getLogger(__name__)
    
    def send_file_transfer_request(self, target_ip: str, src_name: str = "Scanner", dst_name: str = "", timeout: float = 5.0) -> Tuple[bool, Optional[ScannerProtocolMessage]]:
        """
        Send a file transfer request to a specific agent and wait for response
        
        Args:
            target_ip: IP address of the target agent
            src_name: Source name for the message
            dst_name: Destination name for the message
            timeout: How long to wait for response
            
        Returns:
            Tuple of (success, response_message) where response_message is None if no response
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        
        try:
            # Bind to local IP and port 706 for consistency
            sock.bind((self.local_ip, self.port))
            
            # Build and send file transfer request
            request_message = self._build_file_transfer_message(src_name, dst_name)
            request_bytes = request_message.to_bytes()
            
            self.logger.info(f"Sending file transfer request ({len(request_bytes)} bytes) from {self.local_ip}:{self.port} to {target_ip}:{self.port}")
            self.logger.debug(f"Message type: {request_message.type_of_request.hex()} (should be 5a5400)")
            
            sock.sendto(request_bytes, (target_ip, self.port))
            
            # Listen for response
            response = self._listen_for_response(sock, target_ip, timeout)
            
            if response:
                self.logger.info(f"Received response from {target_ip}")
                return True, response
            else:
                self.logger.warning(f"No response received from {target_ip} within {timeout} seconds")
                return True, None  # Sent successfully but no response
                
        except Exception as e:
            self.logger.error(f"Failed to send file transfer request to {target_ip}: {e}")
            return False, None
        finally:
            sock.close()
    
    def _build_file_transfer_message(self, src_name: str, dst_name: str) -> ScannerProtocolMessage:
        """Build a file transfer message using the builder pattern."""
        builder = ScannerProtocolMessageBuilder()
        return builder.build_file_transfer_message(self.local_ip, src_name, dst_name)
    
    def _listen_for_response(self, sock: socket.socket, target_ip: str, timeout: float) -> Optional[ScannerProtocolMessage]:
        """Listen for file transfer response from the target agent."""
        start_time = time.time()
        
        self.logger.info(f"Listening for response from {target_ip} for {timeout} seconds...")
        
        while time.time() - start_time < timeout:
            try:
                resp, addr = sock.recvfrom(1024)
                
                # Only accept responses from the target IP
                if addr[0] == target_ip:
                    self.logger.info(f"=== RESPONSE FROM {addr[0]}:{addr[1]} ===")
                    try:
                        response_message = ScannerProtocolMessage.from_bytes(resp)
                        self.logger.info(f"Successfully parsed response from {addr}")
                        self.logger.debug(f"Response type: {response_message.type_of_request.hex()}")
                        return response_message
                    except Exception as e:
                        self.logger.error(f"Failed to parse response from {addr}: {e}")
                        self.logger.debug(f"Raw response: {resp.hex()}")
                else:
                    self.logger.debug(f"Ignoring response from unexpected IP {addr[0]} (expecting {target_ip})")
                
            except socket.timeout:
                continue
                
        return None
