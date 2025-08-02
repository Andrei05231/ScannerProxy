"""
Agent discovery response service.
Follows SRP - Single responsibility for responding to discovery operations.
This is the counterpart to AgentDiscoveryService - it listens and responds instead of broadcasting and listening.
"""
import socket
import threading
import time
import logging
from typing import Optional, Callable, Any
from pathlib import Path
from datetime import datetime

from ..dto.network_models import ScannerProtocolMessage
from ..network.protocols.message_builder import ScannerProtocolMessageBuilder
from ..utils.config import config


class AgentDiscoveryResponseService:
    """Service for responding to discovery broadcasts from scanners and handling file transfers."""
    
    def __init__(self, local_ip: str, port: int, agent_name: str = None):
        """
        Initialize the discovery response service.
        
        Args:
            local_ip: Local IP address to bind to
            port: UDP port to listen on (typically 706)
            agent_name: Name of this agent (uses config default if None)
        """
        self.local_ip = local_ip
        self.port = port
        self.tcp_port = config.get('network.tcp_port', 708)
        self.agent_name = agent_name or config.get('scanner.default_src_name', 'Agent')
        self.files_directory = config.get('scanner.files_directory', 'received_files')
        self.logger = logging.getLogger(__name__)
        
        # UDP socket for discovery/file transfer requests
        self._udp_socket: Optional[socket.socket] = None
        self._running = False
        self._udp_thread: Optional[threading.Thread] = None
        
        # TCP server for file transfers
        self._tcp_socket: Optional[socket.socket] = None
        self._tcp_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self._discovery_callback: Optional[Callable[[ScannerProtocolMessage, str], Any]] = None
        self._file_transfer_callback: Optional[Callable[[ScannerProtocolMessage, str], Any]] = None
        
        # Ensure files directory exists
        Path(self.files_directory).mkdir(parents=True, exist_ok=True)
    
    def set_discovery_callback(self, callback: Callable[[ScannerProtocolMessage, str], Any]) -> None:
        """
        Set callback function to be called when discovery message is received.
        
        Args:
            callback: Function that takes (message, sender_address) and returns response data or None
        """
        self._discovery_callback = callback

    def set_file_transfer_callback(self, callback: Callable[[ScannerProtocolMessage, str], Any]) -> None:
        """
        Set callback function to be called when file transfer request is received.
        
        Args:
            callback: Function that takes (message, sender_address) and returns response data or None
        """
        self._file_transfer_callback = callback
    
    def start(self) -> bool:
        """
        Start listening for discovery broadcasts.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            self.logger.warning("Discovery response service is already running")
            return True
        
        try:
            # Setup UDP socket for discovery and file transfer requests
            self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._udp_socket.bind(('0.0.0.0', self.port))  # Listen on all interfaces
            self._udp_socket.settimeout(1.0)  # Set timeout for clean shutdown

            # Setup TCP socket for file transfers
            self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._tcp_socket.bind((self.local_ip, self.tcp_port))
            self._tcp_socket.listen(5)
            self._tcp_socket.settimeout(1.0)  # Set timeout for clean shutdown

            self._running = True
            
            # Start UDP listener thread
            self._udp_thread = threading.Thread(target=self._udp_listen_loop, daemon=True)
            self._udp_thread.start()
            
            # Start TCP listener thread  
            self._tcp_thread = threading.Thread(target=self._tcp_listen_loop, daemon=True)
            self._tcp_thread.start()

            self.logger.info(f"Discovery response service started on UDP port {self.port} and TCP port {self.tcp_port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start discovery response service: {e}")
            self._cleanup()
            return False
    
    def stop(self) -> None:
        """Stop the discovery response service."""
        if not self._running:
            return
        
        self.logger.info("Stopping discovery response service...")
        self._running = False
        
        # Wait for threads to finish
        if self._udp_thread and self._udp_thread.is_alive():
            self._udp_thread.join(timeout=5.0)
            
        if self._tcp_thread and self._tcp_thread.is_alive():
            self._tcp_thread.join(timeout=5.0)
        
        self._cleanup()
        self.logger.info("Discovery response service stopped")
    
    def is_running(self) -> bool:
        """Check if the service is currently running."""
        return self._running
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self._udp_socket:
                self._udp_socket.close()
                self._udp_socket = None
        except Exception:
            pass
            
        try:
            if self._tcp_socket:
                self._tcp_socket.close()
                self._tcp_socket = None
        except Exception:
            pass
            
        # Legacy cleanup for backward compatibility
        if hasattr(self, '_socket') and self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
    
    def _udp_listen_loop(self) -> None:
        """UDP listening loop - runs in separate thread."""
        self.logger.info(f"Starting UDP listener on port {self.port}")
        
        while self._running:
            try:
                data, addr = self._udp_socket.recvfrom(config.get('network.buffer_size', 1024))
                self.logger.debug(f"Received {len(data)} bytes from {addr[0]}:{addr[1]}")
                
                # Process the received message
                self._handle_udp_message(data, addr)
                
            except socket.timeout:
                # Timeout is expected for clean shutdown
                continue
            except Exception as e:
                if self._running:  # Only log if we're supposed to be running
                    self.logger.error(f"Error in UDP listener: {e}")
        
        self.logger.info("UDP listener stopped")

    def _tcp_listen_loop(self) -> None:
        """TCP listening loop for file transfers - runs in separate thread."""
        self.logger.info(f"Starting TCP listener on {self.local_ip}:{self.tcp_port}")
        
        while self._running:
            try:
                client_socket, client_addr = self._tcp_socket.accept()
                self.logger.info(f"TCP connection accepted from {client_addr[0]}:{client_addr[1]}")
                
                # Handle file transfer in a separate thread
                transfer_thread = threading.Thread(
                    target=self._handle_file_transfer,
                    args=(client_socket, client_addr),
                    daemon=True
                )
                transfer_thread.start()
                
            except socket.timeout:
                # Timeout is expected for clean shutdown
                continue
            except Exception as e:
                if self._running:
                    self.logger.error(f"Error in TCP listener: {e}")
        
        self.logger.info("TCP listener stopped")

    # Legacy method name for backward compatibility
    def _listen_loop(self) -> None:
        """Legacy method - delegates to UDP listener."""
        self._udp_listen_loop()
    
    def _handle_udp_message(self, data: bytes, addr: tuple) -> None:
        """
        Handle incoming UDP message (discovery or file transfer request).
        
        Args:
            data: Raw message data
            addr: Sender address tuple (ip, port)
        """
        try:
            # Try to parse the message
            message = ScannerProtocolMessage.from_bytes(data)
            sender_address = f"{addr[0]}:{addr[1]}"
            
            self.logger.debug(f"Message type: {message.type_of_request.hex()}")
            
            # Check message type
            if message.type_of_request == bytes.fromhex('5A0000'):
                # Discovery request
                self.logger.info(f"Received discovery message from {sender_address}")
                self._handle_discovery_message(message, addr)
                
            elif message.type_of_request == bytes.fromhex('5A5400'):
                # File transfer request
                self.logger.info(f"Received file transfer request from {sender_address}")
                self._handle_file_transfer_request(message, addr)
                
            else:
                self.logger.warning(f"Unknown message type: {message.type_of_request.hex()} from {sender_address}")
                
        except Exception as e:
            self.logger.error(f"Error parsing message from {addr[0]}:{addr[1]}: {e}")
            self.logger.debug(f"Raw data: {data.hex()}")

    def _handle_discovery_message(self, message: ScannerProtocolMessage, addr: tuple) -> None:
        """
        Handle discovery message and send response.
        
        Args:
            message: Parsed scanner protocol message
            addr: Sender address tuple (ip, port)
        """
        try:
            sender_address = f"{addr[0]}:{addr[1]}"
            
            # Check if this is a discovery request
            if self._is_discovery_request(message):
                response_message = self._build_discovery_response(message, addr[0])
                
                # Call custom callback if set
                if self._discovery_callback:
                    try:
                        callback_result = self._discovery_callback(message, sender_address)
                        if callback_result is not None:
                            # Callback can modify the response or provide additional data
                            self.logger.debug(f"Discovery callback returned: {callback_result}")
                    except Exception as e:
                        self.logger.error(f"Error in discovery callback: {e}")
                
                # Send response back to sender
                self._send_response(response_message, addr)
            else:
                self.logger.debug(f"Ignoring non-discovery message from {sender_address}")
                
        except Exception as e:
            self.logger.error(f"Failed to handle discovery message from {addr}: {e}")

    def _handle_file_transfer_request(self, message: ScannerProtocolMessage, addr: tuple) -> None:
        """
        Handle file transfer request message.
        
        Args:
            message: Parsed scanner protocol message
            addr: Sender address tuple (ip, port)
        """
        try:
            sender_address = f"{addr[0]}:{addr[1]}"
            
            # Build and send UDP response to acknowledge file transfer request
            response_message = self._build_file_transfer_response(message, addr[0])
            self._send_response(response_message, addr)
            
            # Call custom callback if set
            if self._file_transfer_callback:
                try:
                    callback_result = self._file_transfer_callback(message, sender_address)
                    if callback_result is not None:
                        self.logger.debug(f"File transfer callback returned: {callback_result}")
                except Exception as e:
                    self.logger.error(f"Error in file transfer callback: {e}")
            
            # Log file transfer initiation
            self.logger.info(f"File transfer request acknowledged for {sender_address}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle file transfer request from {addr}: {e}")

    def _handle_file_transfer(self, client_socket: socket.socket, client_addr: tuple) -> None:
        """
        Handle incoming file transfer via TCP.
        
        Args:
            client_socket: TCP socket connected to client
            client_addr: Client address tuple (ip, port)
        """
        try:
            sender_address = f"{client_addr[0]}:{client_addr[1]}"
            self.logger.info(f"Starting file transfer from {sender_address}")
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"received_file_{timestamp}_{client_addr[0].replace('.', '_')}.raw"
            filepath = Path(self.files_directory) / filename
            
            # Receive file data
            total_bytes = 0
            with open(filepath, 'wb') as f:
                while True:
                    data = client_socket.recv(8192)  # 8KB chunks
                    if not data:
                        break
                    f.write(data)
                    total_bytes += len(data)
            
            self.logger.info(f"File transfer completed: {filename} ({total_bytes} bytes)")
            
        except Exception as e:
            self.logger.error(f"Error in file transfer from {client_addr}: {e}")
        finally:
            try:
                client_socket.close()
            except Exception:
                pass
    
    def _is_discovery_request(self, message: ScannerProtocolMessage) -> bool:
        """
        Check if the message is a discovery request.
        
        Args:
            message: Parsed scanner protocol message
            
        Returns:
            True if this is a discovery request
        """
        # Discovery requests have type 0x5A 0x00 0x00
        return message.type_of_request == b'\x5a\x00\x00'
    
    def _build_discovery_response(self, original_message: ScannerProtocolMessage, sender_ip: str) -> ScannerProtocolMessage:
        """
        Build a response message to the discovery request.
        
        Args:
            original_message: The original discovery message received
            sender_ip: IP address of the sender
            
        Returns:
            Response message to send back
        """
        builder = ScannerProtocolMessageBuilder()
        
        # Use sender's name from the original request as source name
        sender_name = original_message.src_name.decode('ascii', errors='ignore')
        
        # Build response with sender's name as src and our agent name as dst
        return (builder.reset()
                .with_discovery_request()
                .with_reserved1(bytes.fromhex('0009b9002c84'))  # Set specific reserved1 value
                .with_initiator_ip(self.local_ip)
                .with_reserved2(bytes.fromhex('000002c4'))      # Set specific reserved2 value
                .with_src_name(sender_name)
                .with_dst_name(self.agent_name)
                .build())

    def _build_file_transfer_response(self, original_message: ScannerProtocolMessage, sender_ip: str) -> ScannerProtocolMessage:
        """
        Build a response message to the file transfer request.
        
        Args:
            original_message: The original file transfer request message received
            sender_ip: IP address of the sender
            
        Returns:
            Response message to send back (same signature as file transfer request)
        """
        builder = ScannerProtocolMessageBuilder()
        
        # Use sender's name from the original request as source name
        sender_name = original_message.src_name.decode('ascii', errors='ignore')
        
        # Build response with same signature as file transfer request (0x5A5400)
        # This acknowledges the file transfer request and indicates we're ready to receive
        return (builder.reset()
                .with_file_transfer_request()  # Use file transfer signature 0x5A5400
                .with_reserved1(bytes.fromhex('0009b9002c84'))  # Set specific reserved1 value
                .with_initiator_ip(self.local_ip)
                .with_reserved2(bytes.fromhex('000002c4'))      # Set specific reserved2 value
                .with_src_name(sender_name)
                .with_dst_name(self.agent_name)
                .build())
    
    def _send_response(self, response_message: ScannerProtocolMessage, addr: tuple) -> None:
        """
        Send response message back to the sender.
        
        Args:
            response_message: Message to send
            addr: Address tuple (ip, port) to send to
        """
        try:
            response_bytes = response_message.to_bytes()
            self._udp_socket.sendto(response_bytes, addr)
            
            self.logger.info(f"Sent UDP response ({len(response_bytes)} bytes) to {addr[0]}:{addr[1]}")
            self.logger.debug(f"Response type: {response_message.type_of_request.hex()}")
            
        except Exception as e:
            self.logger.error(f"Failed to send UDP response to {addr}: {e}")
