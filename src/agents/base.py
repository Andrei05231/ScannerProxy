"""
Base agent interfaces and abstract classes.
Follows LSP - Liskov Substitution Principle and ISP - Interface Segregation Principle.
"""
from abc import ABC, abstractmethod
from typing import Protocol, Any, Dict


class Discoverable(Protocol):
    """Interface for discoverable agents - ISP: Interface segregation"""
    def respond_to_discovery(self, discovery_message: Any) -> Any:
        """Respond to a discovery request"""
        ...


class DocumentHandler(Protocol):
    """Interface for document handling - ISP: Interface segregation"""
    def handle_document(self, document: Any) -> bool:
        """Handle incoming document"""
        ...


class Configurable(Protocol):
    """Interface for configurable components - ISP: Interface segregation"""
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the component"""
        ...


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Follows LSP - Any subclass should be substitutable for BaseAgent.
    """
    
    def __init__(self, name: str, ip_address: str, port: int):
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.is_running = False
    
    @abstractmethod
    def start(self) -> None:
        """Start the agent"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the agent"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, ip={self.ip_address}, port={self.port})"


class NetworkAgent(BaseAgent):
    """Base class for network-enabled agents"""
    
    def __init__(self, name: str, ip_address: str, port: int):
        super().__init__(name, ip_address, port)
        self.socket = None
    
    @abstractmethod
    def bind_socket(self) -> None:
        """Bind to network socket"""
        pass
    
    @abstractmethod
    def listen_for_connections(self) -> None:
        """Listen for incoming connections"""
        pass
