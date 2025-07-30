"""
Main application module.
"""
import logging
from .core.scanner_service import ScannerService
from .utils.config import config


def setup_logging():
    """Setup logging configuration"""
    log_level = config.get('logging.level', 'INFO')
    log_format = config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format
    )


def print_discovery_summary(discovered_agents):
    """Print a summary of discovered agents"""
    print("\n=== DISCOVERY SUMMARY ===")
    if discovered_agents:
        print(f"Found {len(discovered_agents)} agent(s) listening for scanned documents:")
        for i, (message, address) in enumerate(discovered_agents, 1):
            print(f"{i}. Agent at {address}")
            print(f"   Source Name: {message.src_name.decode('ascii', errors='ignore')}")
            print(f"   Destination Name: {message.dst_name.decode('ascii', errors='ignore')}")
            print(f"   IP: {message.initiator_ip}")
    else:
        print("No agents discovered on the network listening for scanned documents.")


def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create and initialize scanner service
        scanner_service = ScannerService()
        scanner_service.initialize()
        
        # Display network status
        network_status = scanner_service.get_network_status()
        print(f"Local IP: {network_status['local_ip']}")
        print(f"Broadcast IP: {network_status['broadcast_ip']}")
        print(f"Interface: {network_status['interface_name']}")
        print("Starting agent discovery...")
        print()
        
        # Discover agents on the network
        discovered_agents = scanner_service.discover_agents()
        
        # Print summary
        print_discovery_summary(discovered_agents)
        
    except Exception as e:
        logger.error(f"Scanner operation failed: {e}")
        return 1
    
    return 0
