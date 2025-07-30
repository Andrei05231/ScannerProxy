"""
Scanner protocol implementation.
Follows SRP - Single responsibility for protocol operations.
"""
from ipaddress import IPv4Address
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...dto.network_models import ScannerProtocolMessage, ProtocolConstants

# Import at runtime to avoid circular imports
def get_protocol_constants():
    from ...dto.network_models import ProtocolConstants
    return ProtocolConstants

def get_scanner_protocol_message():
    from ...dto.network_models import ScannerProtocolMessage
    return ScannerProtocolMessage


class MessageSerializer:
    """Handles message serialization - SRP: Single responsibility for serialization"""
    
    @staticmethod
    def serialize_message(message: "ScannerProtocolMessage") -> bytes:
        """Convert message to bytes representation"""
        ProtocolConstants = get_protocol_constants()
        
        ip_bytes = message.initiator_ip.packed
        src_bytes = message.src_name.ljust(ProtocolConstants.SRC_NAME_SIZE, b'\x00')
        dst_bytes = message.dst_name.ljust(ProtocolConstants.DST_NAME_SIZE, b'\x00')
        
        return (
            message.signature +
            message.type_of_request +
            message.reserved1 +
            ip_bytes +
            message.reserved2 +
            src_bytes +
            dst_bytes +
            message.reserved3
        )


class MessageDeserializer:
    """Handles message deserialization - SRP: Single responsibility for deserialization"""
    
    @staticmethod
    def deserialize_message(data: bytes) -> "ScannerProtocolMessage":
        """Create message from bytes representation"""
        ProtocolConstants = get_protocol_constants()
        ScannerProtocolMessage = get_scanner_protocol_message()
        
        if len(data) != ProtocolConstants.EXPECTED_MESSAGE_SIZE:
            raise ValueError(f"Expected {ProtocolConstants.EXPECTED_MESSAGE_SIZE} bytes, got {len(data)}")

        signature = data[0:3]
        type_of_request = data[3:6]
        reserved1 = data[6:12]
        ip_bytes = data[12:16]
        initiator_ip = IPv4Address(ip_bytes)
        reserved2 = data[16:20]
        src_name = data[20:40].rstrip(b'\x00')
        dst_name = data[40:80].rstrip(b'\x00')
        reserved3 = data[80:90]

        return ScannerProtocolMessage(
            signature=signature,
            type_of_request=type_of_request,
            reserved1=reserved1,
            initiator_ip=initiator_ip,
            reserved2=reserved2,
            src_name=src_name,
            dst_name=dst_name,
            reserved3=reserved3
        )


class MessageDebugger:
    """Handles message debugging - SRP: Single responsibility for debugging"""
    
    @staticmethod
    def get_debug_info(message: "ScannerProtocolMessage") -> str:
        """Generate debug information for the message"""
        debug_lines = [
            f"Signature: {len(message.signature)} bytes - {message.signature.hex()}",
            f"Type of Request: {len(message.type_of_request)} bytes - {message.type_of_request.hex()}",
            f"Reserved1: {len(message.reserved1)} bytes - {message.reserved1.hex()}",
            f"Initiator IP: {message.initiator_ip} (4 bytes: {message.initiator_ip.packed.hex()})",
            f"Reserved2: {len(message.reserved2)} bytes - {message.reserved2.hex()}",
            f"Source Name: {len(message.src_name)} bytes - {message.src_name.hex()}",
            f"Destination Name: {len(message.dst_name)} bytes - {message.dst_name.hex()}",
            f"Reserved3: {len(message.reserved3)} bytes - {message.reserved3.hex()}"
        ]
        return "\n".join(debug_lines)

    @staticmethod
    def print_debug_info(message: "ScannerProtocolMessage") -> None:
        """Print debug information for the message"""
        print(MessageDebugger.get_debug_info(message))
