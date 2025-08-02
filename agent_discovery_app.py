"""
Agent Discovery Response Service.
A headless service that listens for discovery broadcasts and responds to them.
This is the counterpart to mock_scanner - it runs as a background service.
"""
import logging
import sys
import signal
import time
from pathlib import Path
from typing import Optional

# Add src to Python path for imports when running as script
if __name__ == "__main__":
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))

# Import using relative paths when run as module, absolute when run as script
try:
    from src.services.agent_discovery_response import AgentDiscoveryResponseService
    from src.network.interfaces import NetworkInterfaceManager
    from src.utils.config import config
    from src.utils.logging_setup import setup_logging
    from src.dto.network_models import ScannerProtocolMessage
except ImportError:
    from services.agent_discovery_response import AgentDiscoveryResponseService
    from network.interfaces import NetworkInterfaceManager
    from utils.config import config
    from utils.logging_setup import setup_logging
    from dto.network_models import ScannerProtocolMessage

# Global discovery service instance
discovery_service: Optional[AgentDiscoveryResponseService] = None


def discovery_callback(message: ScannerProtocolMessage, sender_address: str) -> dict:
    """
    Callback function called when discovery message is received.
    
    Args:
        message: The discovery message received
        sender_address: Address of the sender
        
    Returns:
        Dictionary with information about the discovery event
    """
    logger = logging.getLogger(__name__)
    sender_name = message.src_name.decode('ascii', errors='ignore')
    
    logger.info(f"Discovery request received from {sender_name} at {sender_address}")
    logger.debug(f"Message details - Type: {message.type_of_request.hex()}, IP: {message.initiator_ip}")
    
    return {
        "sender_name": sender_name,
        "sender_ip": str(message.initiator_ip),
        "sender_address": sender_address,
        "timestamp": time.time()
    }


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global discovery_service
    
    logger = logging.getLogger(__name__)
    logger.info("Received shutdown signal, stopping service...")
    
    if discovery_service and discovery_service.is_running():
        discovery_service.stop()
    
    logger.info("Service stopped. Exiting.")
    sys.exit(0)


def main():
    """Main service entry point"""
    global discovery_service
    
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Agent Discovery Response Service")
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Get network configuration
        logger.info("Initializing network interface...")
        network_manager = NetworkInterfaceManager()
        local_ip, broadcast_ip, interface_name = network_manager.get_default_interface_info()
        
        # Get configuration
        udp_port = config.get('network.udp_port', 706)
        agent_name = config.get('scanner.default_src_name', 'ResponseAgent')
        
        logger.info(f"Network configuration - IP: {local_ip}, Interface: {interface_name}, Port: {udp_port}")
        logger.info(f"Agent name: {agent_name}")
        
        # Create and start discovery service
        logger.info("Creating discovery response service...")
        discovery_service = AgentDiscoveryResponseService(
            local_ip=local_ip,
            port=udp_port,
            agent_name=agent_name
        )
        
        # Set the discovery callback
        discovery_service.set_discovery_callback(discovery_callback)
        
        logger.info("Starting discovery response service...")
        success = discovery_service.start()
        
        if success:
            logger.info(f"Discovery Response Service started successfully on {local_ip}:{udp_port}")
            logger.info("Service is now listening for discovery broadcasts...")
            
            # Keep the service running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                signal_handler(signal.SIGINT, None)
                
        else:
            logger.error("Failed to start discovery response service")
            return 1
            
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
