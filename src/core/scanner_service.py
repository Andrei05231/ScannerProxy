"""
Main scanner service orchestrator.
Follows SRP - Single responsibility for coordinating scanner operations.
Follows DIP - Depends on abstractions, not concretions.
"""
from typing import List, Tuple, Dict, Any, Optional
import logging

from ..network.interfaces import NetworkInterfaceManager
from ..network.discovery import AgentDiscoveryService
from ..services.file_transfer import FileTransferService
from ..dto.network_models import ScannerProtocolMessage
from ..utils.config import config


class ScannerService:
    """
    Main service that orchestrates scanner operations.
    Follows DIP by depending on abstractions (interfaces) rather than concrete implementations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.network_manager = NetworkInterfaceManager()
        self.local_ip: str = ""
        self.broadcast_ip: str = ""
        self.interface_name: str = ""
        self.discovery_service: AgentDiscoveryService = None
        self.file_transfer_service: FileTransferService = None
        
    def initialize(self) -> None:
        """Initialize the scanner service"""
        try:
            # Get network configuration
            self.local_ip, self.broadcast_ip, self.interface_name = self.network_manager.get_default_interface_info()
            
            # Initialize discovery service
            udp_port = config.get('network.udp_port', 706)
            tcp_port = config.get('network.tcp_port', 708)
            self.discovery_service = AgentDiscoveryService(
                local_ip=self.local_ip,
                broadcast_ip=self.broadcast_ip,
                port=udp_port
            )
            
            # Initialize file transfer service
            self.file_transfer_service = FileTransferService(
                local_ip=self.local_ip,
                port=udp_port,
                tcp_port=tcp_port
            )
            
            self.logger.info(f"Scanner service initialized on interface {self.interface_name}")
            self.logger.info(f"Local IP: {self.local_ip}, Broadcast IP: {self.broadcast_ip}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scanner service: {e}")
            raise
    
    def discover_agents(self) -> List[Tuple[ScannerProtocolMessage, str]]:
        """
        Discover available agents on the network.
        
        Returns:
            List of discovered agents with their response messages and addresses
        """
        if not self.discovery_service:
            raise RuntimeError("Scanner service not initialized. Call initialize() first.")
        
        timeout = config.get('network.discovery_timeout', 10.0)
        src_name = config.get('scanner.default_src_name', 'Scanner')
        
        self.logger.info("Starting agent discovery...")
        
        discovered_agents = self.discovery_service.discover_agents(
            timeout=timeout,
            src_name=src_name
        )
        
        self.logger.info(f"Discovery completed. Found {len(discovered_agents)} agents.")
        
        return discovered_agents
    
    def send_file_transfer_request(self, target_ip: str, src_name: str = None, dst_name: str = "", file_path: str = None, progress_callback=None) -> Tuple[bool, Optional[ScannerProtocolMessage]]:
        """
        Send a file transfer request to a specific agent and wait for response
        
        Args:
            target_ip: IP address of the target agent
            src_name: Source name for the message (uses config default if None)
            dst_name: Destination name for the message
            file_path: Path to the file to send (uses config default if None)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (success, response_message) where response_message is None if no response
        """
        if not self.file_transfer_service:
            self.logger.error("File transfer service not initialized")
            return False, None
        
        # Use config defaults if not provided
        if src_name is None:
            src_name = config.get('scanner.default_src_name', 'Scanner')
        if file_path is None:
            file_path = config.get('scanner.default_file_path', 'scan.raw')
        
        self.logger.info(f"Sending file transfer request to {target_ip} for file {file_path}")
        
        success, response = self.file_transfer_service.send_file_transfer_request(
            target_ip=target_ip,
            src_name=src_name,
            dst_name=dst_name,
            file_path=file_path,
            progress_callback=progress_callback
        )
        
        if success:
            if response:
                self.logger.info(f"File transfer request sent successfully to {target_ip} with response")
            else:
                self.logger.info(f"File transfer request sent successfully to {target_ip} but no response received")
        else:
            self.logger.error(f"Failed to send file transfer request to {target_ip}")
        
        return success, response
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get current network status information"""
        return {
            "local_ip": self.local_ip,
            "broadcast_ip": self.broadcast_ip,
            "interface_name": self.interface_name,
            "is_initialized": self.discovery_service is not None
        }
    
    def get_available_interfaces(self) -> List[str]:
        """Get list of available network interfaces"""
        return self.network_manager.list_available_interfaces()
