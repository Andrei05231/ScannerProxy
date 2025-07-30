from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, field_validator
from typing import ClassVar, Protocol
from ipaddress import IPv4Address, AddressValueError
import socket


class ProtocolConstants:
    """Constants for the scanner protocol - SRP: Single responsibility for constants"""
    SIGNATURE: bytes = b'\x55\x00\x00'
    TYPE_OF_REQUEST: bytes = b'\x5a\x00\x00'
    EXPECTED_MESSAGE_SIZE: int = 90
    SRC_NAME_SIZE: int = 20
    DST_NAME_SIZE: int = 40
    RESERVED1_SIZE: int = 6
    RESERVED2_SIZE: int = 4
    RESERVED3_SIZE: int = 10
    IP_SIZE: int = 4


class Serializable(Protocol):
    """Interface for serializable objects - ISP: Interface segregation"""
    def to_bytes(self) -> bytes:
        ...


class Deserializable(Protocol):
    """Interface for deserializable objects - ISP: Interface segregation"""
    @classmethod
    def from_bytes(cls, data: bytes) -> "Deserializable":
        ...


class Debuggable(Protocol):
    """Interface for debuggable objects - ISP: Interface segregation"""
    def debug_info(self) -> str:
        ...


class FieldValidator:
    """Utility class for field validation - SRP: Single responsibility for validation"""
    
    @staticmethod
    def validate_ip_address(value) -> IPv4Address:
        """Validate and convert IP address input"""
        if isinstance(value, str):
            try:
                return IPv4Address(value)
            except AddressValueError as e:
                raise ValueError(f"Invalid IP address: {value}") from e
        elif isinstance(value, IPv4Address):
            return value
        else:
            raise ValueError(f"IP address must be string or IPv4Address, got {type(value)}")

    @staticmethod
    def validate_bytes_field(value: bytes, max_length: int, field_name: str) -> bytes:
        """Validate bytes field length"""
        if len(value) > max_length:
            raise ValueError(f"{field_name} exceeds maximum length of {max_length} bytes")
        return value


class MessageSerializer:
    """Handles message serialization - SRP: Single responsibility for serialization"""
    
    @staticmethod
    def serialize_message(message: "ScannerProtocolMessage") -> bytes:
        """Convert message to bytes representation"""
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


class ScannerProtocolMessage(BaseModel):
    """
    Scanner protocol message model - SRP: Single responsibility for data structure
    OCP: Open for extension through composition with serializer/deserializer classes
    """
    
    signature: bytes = Field(default=ProtocolConstants.SIGNATURE)
    type_of_request: bytes = Field(default=ProtocolConstants.TYPE_OF_REQUEST)
    reserved1: bytes = Field(default=b'\x00' * ProtocolConstants.RESERVED1_SIZE)
    initiator_ip: IPv4Address = Field(default=IPv4Address("192.168.1.137"))
    reserved2: bytes = Field(default=b'\x00' * ProtocolConstants.RESERVED2_SIZE)
    src_name: bytes = Field(default=b"L24e")
    dst_name: bytes = Field(default=b"")
    reserved3: bytes = Field(default=b'\x00' * ProtocolConstants.RESERVED3_SIZE)

    @field_validator('initiator_ip')
    @classmethod
    def validate_ip(cls, v) -> IPv4Address:
        return FieldValidator.validate_ip_address(v)

    @field_validator('src_name')
    @classmethod
    def validate_src_name(cls, v) -> bytes:
        return FieldValidator.validate_bytes_field(v, ProtocolConstants.SRC_NAME_SIZE, "src_name")

    @field_validator('dst_name')
    @classmethod
    def validate_dst_name(cls, v) -> bytes:
        return FieldValidator.validate_bytes_field(v, ProtocolConstants.DST_NAME_SIZE, "dst_name")

    def to_bytes(self) -> bytes:
        """Serialize message to bytes - DIP: Depends on abstraction (MessageSerializer)"""
        return MessageSerializer.serialize_message(self)
    
    def debug_info(self) -> str:
        """Get debug information - DIP: Depends on abstraction (MessageDebugger)"""
        return MessageDebugger.get_debug_info(self)
    
    def debug(self) -> None:
        """Print debug information"""
        MessageDebugger.print_debug_info(self)

    @classmethod
    def from_bytes(cls, data: bytes) -> "ScannerProtocolMessage":
        """Deserialize message from bytes - DIP: Depends on abstraction (MessageDeserializer)"""
        return MessageDeserializer.deserialize_message(data)
