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
from pathlib import Path
import humanize

from ..dto.network_models import ScannerProtocolMessage, ProtocolConstants
from ..network.protocols.message_builder import ScannerProtocolMessageBuilder
from ..utils.config import config


class FileTransferService:
    """
    Handles file transfer operations - SRP: Single responsibility for file transfer
    Follows the same pattern as AgentDiscoveryService for code reusability
    """
    
    def __init__(self, local_ip: str, port: int = 706, tcp_port: int = 708):
        """
        Initialize file transfer service
        
        Args:
            local_ip: Local IP address for sending
            port: UDP port number for communication (default: 706)
            tcp_port: TCP port number for file transfer (default: 708)
        """
        self.local_ip = local_ip
        self.port = port
        self.tcp_port = tcp_port
        self.logger = logging.getLogger(__name__)
    
    def send_file_transfer_request(self, target_ip: str, src_name: str = None, dst_name: str = "", timeout: float = None, file_path: str = None, progress_callback=None) -> Tuple[bool, Optional[ScannerProtocolMessage]]:
        """
        Send a file transfer request to a specific agent and wait for response
        
        Args:
            target_ip: IP address of the target agent
            src_name: Source name for the message (uses config default if None)
            dst_name: Destination name for the message
            timeout: How long to wait for response (uses config default if None)
            file_path: Path to the file to send (uses config default if None)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (success, response_message) where response_message is None if no response
        """
        # Use config defaults if not provided
        if src_name is None:
            src_name = config.get('scanner.default_src_name', 'Scanner')
        if timeout is None:
            timeout = config.get('network.discovery_timeout', 5.0)
        if file_path is None:
            file_path = config.get('scanner.default_file_path', 'scan.raw')
            
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(config.get('network.socket_timeout', 1.0))
        
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
                self.logger.info(f"Received UDP response from {target_ip}, initiating TCP connection on port {self.tcp_port}")
                
                # Initiate TCP connection for actual file transfer
                tcp_success = self._initiate_tcp_connection(target_ip, file_path=file_path, progress_callback=progress_callback)
                
                if tcp_success:
                    self.logger.info(f"TCP connection and file transfer completed successfully with {target_ip}:{self.tcp_port}")
                else:
                    self.logger.warning(f"TCP connection or file transfer failed with {target_ip}:{self.tcp_port}")
                
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
                resp, addr = sock.recvfrom(config.get('network.buffer_size', 1024))
                
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

    def _initiate_tcp_connection(self, target_ip: str, connection_timeout: float = None, file_path: str = None, progress_callback=None) -> bool:
        """
        Initiate TCP connection on port 708 for actual file transfer
        
        Args:
            target_ip: IP address of the target agent
            connection_timeout: Timeout for TCP connection establishment (uses config default if None)
            file_path: Path to the file to send (uses config default if None)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            True if connection and file transfer successful, False otherwise
        """
        # Use config defaults if not provided
        if connection_timeout is None:
            connection_timeout = config.get('network.tcp_connection_timeout', 10.0)
        if file_path is None:
            file_path = config.get('scanner.default_file_path', 'scan.raw')
            
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.settimeout(connection_timeout)
        
        try:
            self.logger.info(f"Attempting TCP connection to {target_ip}:{self.tcp_port}")
            
            # Connect to the agent's TCP port
            tcp_sock.connect((target_ip, self.tcp_port))
            
            self.logger.info(f"TCP connection established with {target_ip}:{self.tcp_port}")
            
            # Send the file immediately after connection is established
            file_sent = self._send_file_over_tcp(tcp_sock, file_path, progress_callback)
            
            if file_sent:
                self.logger.info(f"File {file_path} sent successfully to {target_ip}")
                return True
            else:
                self.logger.error(f"Failed to send file {file_path} to {target_ip}")
                return False
                
        except socket.timeout:
            self.logger.error(f"TCP connection timeout to {target_ip}:{self.tcp_port}")
            return False
        except ConnectionRefusedError:
            self.logger.error(f"TCP connection refused by {target_ip}:{self.tcp_port}")
            return False
        except Exception as e:
            self.logger.error(f"TCP connection error to {target_ip}:{self.tcp_port}: {e}")
            return False
        finally:
            tcp_sock.close()
            self.logger.info(f"TCP connection closed with {target_ip}:{self.tcp_port}")

    def _send_file_over_tcp(self, tcp_sock: socket.socket, file_path: str, progress_callback=None) -> bool:
        """
        Send file contents over established TCP connection
        
        Args:
            tcp_sock: Established TCP socket
            file_path: Path to the file to send
            progress_callback: Optional callback function for progress updates (bytes_sent, total_bytes)
            
        Returns:
            True if file sent successfully, False otherwise
        """
        try:
            # Check if file exists using pathlib
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                self.logger.error(f"File {file_path} does not exist")
                return False
            
            file_size = file_path_obj.stat().st_size
            self.logger.info(f"Preparing to send file {file_path} ({humanize.naturalsize(file_size)})")
            
            # Send file contents directly in chunks without protocol messages
            chunk_size = config.get('network.tcp_chunk_size', 8192)
            bytes_sent = 0
            
            with file_path_obj.open('rb') as file:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    
                    tcp_sock.sendall(chunk)
                    bytes_sent += len(chunk)
                    
                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(bytes_sent, file_size)
                    
                    # Log progress periodically (less frequent now since we have visual progress)
                    if bytes_sent % (chunk_size * 50) == 0:  # Log every ~400KB instead of every 80KB
                        progress = (bytes_sent / file_size) * 100
                        self.logger.debug(f"File transfer progress: {bytes_sent}/{file_size} bytes ({progress:.1f}%)")
            
            # Final progress update
            if progress_callback:
                progress_callback(file_size, file_size)
                
            self.logger.info(f"File transfer completed successfully: {bytes_sent} bytes sent")
            return True
                
        except Exception as e:
            self.logger.error(f"Error sending file over TCP: {e}")
            return False
