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

from ..dto.network_models import ScannerProtocolMessage
from ..network.protocols.message_builder import ScannerProtocolMessageBuilder
from ..utils.config import config


class AgentDiscoveryResponseService:
    """Service for responding to discovery broadcasts from scanners."""
    
    def __init__(self, local_ip: str, port: int, agent_name: str = None):
        """
        Initialize the discovery response service.
        
        Args:
            local_ip: Local IP address to bind to
            port: Port to listen on (typically 706)
            agent_name: Name of this agent (uses config default if None)
        """
        self.local_ip = local_ip
        self.port = port
        self.agent_name = agent_name or config.get('scanner.default_src_name', 'Agent')
        self.logger = logging.getLogger(__name__)
        self._socket: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._discovery_callback: Optional[Callable[[ScannerProtocolMessage, str], Any]] = None
    
    def set_discovery_callback(self, callback: Callable[[ScannerProtocolMessage, str], Any]) -> None:
        """
        Set callback function to be called when discovery message is received.
        
        Args:
            callback: Function that takes (message, sender_address) and returns response data or None
        """
        self._discovery_callback = callback
    
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
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._socket.bind(('0.0.0.0', self.port))  # Listen on all interfaces
            self._socket.settimeout(1.0)  # Set timeout for clean shutdown
            
            self._running = True
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
            
            self.logger.info(f"Discovery response service started on port {self.port}")
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
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        
        self._cleanup()
        self.logger.info("Discovery response service stopped")
    
    def is_running(self) -> bool:
        """Check if the service is currently running."""
        return self._running
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
    
    def _listen_loop(self) -> None:
        """Main listening loop - runs in separate thread."""
        self.logger.info(f"Starting discovery listener on {self.local_ip}:{self.port}")
        
        while self._running:
            try:
                data, addr = self._socket.recvfrom(config.get('network.buffer_size', 1024))
                self.logger.debug(f"Received {len(data)} bytes from {addr[0]}:{addr[1]}")
                
                # Process the received message
                self._handle_discovery_message(data, addr)
                
            except socket.timeout:
                # Timeout is expected for clean shutdown
                continue
            except Exception as e:
                if self._running:  # Only log if we're supposed to be running
                    self.logger.error(f"Error in discovery listener: {e}")
    
    def _handle_discovery_message(self, data: bytes, addr: tuple) -> None:
        """
        Handle incoming discovery message and send response.
        
        Args:
            data: Raw message data
            addr: Sender address tuple (ip, port)
        """
        try:
            # Try to parse the message
            message = ScannerProtocolMessage.from_bytes(data)
            sender_address = f"{addr[0]}:{addr[1]}"
            
            self.logger.info(f"Received discovery message from {sender_address}")
            self.logger.debug(f"Message type: {message.type_of_request.hex()}")
            
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
            self.logger.debug(f"Raw message data: {data.hex()}")
    
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
                .with_all_reserved1_zeros()
                .with_initiator_ip(self.local_ip)
                .with_all_reserved2_zeros()
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
            self._socket.sendto(response_bytes, addr)
            
            self.logger.info(f"Sent discovery response ({len(response_bytes)} bytes) to {addr[0]}:{addr[1]}")
            self.logger.debug(f"Response type: {response_message.type_of_request.hex()}")
            
        except Exception as e:
            self.logger.error(f"Failed to send discovery response to {addr}: {e}")
