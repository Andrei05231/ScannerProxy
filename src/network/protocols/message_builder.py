"""
Message builder for scanner protocol messages.
Follows SRP - Single responsibility for building messages.
"""
from ipaddress import IPv4Address
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...dto.network_models import ScannerProtocolMessage, ProtocolConstants

def get_protocol_constants():
    from ...dto.network_models import ProtocolConstants
    return ProtocolConstants

def get_scanner_protocol_message():
    from ...dto.network_models import ScannerProtocolMessage
    return ScannerProtocolMessage


class ScannerProtocolMessageBuilder:
    """Builder pattern for ScannerProtocolMessage - SRP: Single responsibility for building messages"""
    
    def __init__(self):
        self.reset()
    
    def reset(self) -> "ScannerProtocolMessageBuilder":
        """Reset builder to default values"""
        ProtocolConstants = get_protocol_constants()
        
        self._signature = ProtocolConstants.SIGNATURE
        self._type_of_request = ProtocolConstants.TYPE_OF_REQUEST
        self._reserved1 = b'\x00' * ProtocolConstants.RESERVED1_SIZE
        self._initiator_ip = IPv4Address("192.168.1.137")
        self._reserved2 = b'\x00' * ProtocolConstants.RESERVED2_SIZE
        self._src_name = b"L24e"
        self._dst_name = b""
        self._reserved3 = b'\x00' * ProtocolConstants.RESERVED3_SIZE
        return self
    
    def with_signature(self, signature: bytes) -> "ScannerProtocolMessageBuilder":
        """Set signature"""
        self._signature = signature
        return self
    
    def with_type_of_request(self, type_of_request: bytes) -> "ScannerProtocolMessageBuilder":
        """Set type of request"""
        self._type_of_request = type_of_request
        return self
    
    def with_discovery_request(self) -> "ScannerProtocolMessageBuilder":
        """Configure for discovery request - Type: 5a 00 00"""
        self._type_of_request = b'\x5a\x00\x00'
        return self
    
    def with_file_transfer_request(self) -> "ScannerProtocolMessageBuilder":
        """Configure for file transfer request - Type: 5a 54 00"""
        self._type_of_request = b'\x5a\x54\x00'
        return self
    
    def with_all_reserved1_zeros(self) -> "ScannerProtocolMessageBuilder":
        """Set reserved1 to all zeros"""
        ProtocolConstants = get_protocol_constants()
        self._reserved1 = b'\x00' * ProtocolConstants.RESERVED1_SIZE
        return self
    
    def with_initiator_ip(self, ip: str | IPv4Address) -> "ScannerProtocolMessageBuilder":
        """Set initiator IP address"""
        if isinstance(ip, str):
            self._initiator_ip = IPv4Address(ip)
        else:
            self._initiator_ip = ip
        return self
    
    def with_all_reserved2_zeros(self) -> "ScannerProtocolMessageBuilder":
        """Set reserved2 to all zeros"""
        ProtocolConstants = get_protocol_constants()
        self._reserved2 = b'\x00' * ProtocolConstants.RESERVED2_SIZE
        return self
    
    def with_src_name(self, name: str | bytes) -> "ScannerProtocolMessageBuilder":
        """Set source name"""
        if isinstance(name, str):
            self._src_name = name.encode('ascii')
        else:
            self._src_name = name
        return self
    
    def with_dst_name(self, name: str | bytes) -> "ScannerProtocolMessageBuilder":
        """Set destination name"""
        if isinstance(name, str):
            self._dst_name = name.encode('ascii')
        else:
            self._dst_name = name
        return self
    
    def with_all_others_zeros(self) -> "ScannerProtocolMessageBuilder":
        """Set dst_name and reserved3 to all zeros"""
        ProtocolConstants = get_protocol_constants()
        self._dst_name = b""
        self._reserved3 = b'\x00' * ProtocolConstants.RESERVED3_SIZE
        return self
    
    def build_discovery_message(self, local_ip: str, src_name: str = "Test-name") -> "ScannerProtocolMessage":
        """Build a discovery message with the specified parameters"""
        return (self.reset()
                .with_discovery_request()
                .with_all_reserved1_zeros()
                .with_initiator_ip(local_ip)
                .with_all_reserved2_zeros()
                .with_src_name(src_name)
                .with_all_others_zeros()
                .build())
    
    def build_file_transfer_message(self, local_ip: str, src_name: str = "Scanner", dst_name: str = "") -> "ScannerProtocolMessage":
        """Build a file transfer message with the specified parameters"""
        return (self.reset()
                .with_file_transfer_request()
                .with_all_reserved1_zeros()
                .with_initiator_ip(local_ip)
                .with_all_reserved2_zeros()
                .with_src_name(src_name)
                .with_dst_name(dst_name)
                .build())
    
    def build(self) -> "ScannerProtocolMessage":
        """Build the final message"""
        ScannerProtocolMessage = get_scanner_protocol_message()
        
        return ScannerProtocolMessage(
            signature=self._signature,
            type_of_request=self._type_of_request,
            reserved1=self._reserved1,
            initiator_ip=self._initiator_ip,
            reserved2=self._reserved2,
            src_name=self._src_name,
            dst_name=self._dst_name,
            reserved3=self._reserved3
        )
