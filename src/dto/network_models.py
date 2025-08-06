"""
Network-related data models and DTOs.
Follows SRP - Single responsibility for network data structures.
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, field_validator
from typing import ClassVar, Protocol
from ipaddress import IPv4Address, AddressValueError


class ProtocolConstants:
    """Constants for the scanner protocol - SRP: Single responsibility for constants"""
    SIGNATURE: bytes = b'\x55\x00\x00'
    TYPE_OF_REQUEST: bytes = b'\x5a\x00\x00'
    TYPE_OF_FILE_TRANSFER: bytes = b'\x5a\x54\x00'  # New request type for file transfer
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
        """Serialize message to bytes"""
        from ..network.protocols.scanner_protocol import MessageSerializer
        return MessageSerializer.serialize_message(self)
    
    def debug_info(self) -> str:
        """Get debug information"""
        from ..network.protocols.scanner_protocol import MessageDebugger
        return MessageDebugger.get_debug_info(self)
    
    def debug(self) -> None:
        """Print debug information"""
        from ..network.protocols.scanner_protocol import MessageDebugger
        MessageDebugger.print_debug_info(self)

    @classmethod
    def from_bytes(cls, data: bytes) -> "ScannerProtocolMessage":
        """Deserialize message from bytes"""
        from ..network.protocols.scanner_protocol import MessageDeserializer
        return MessageDeserializer.deserialize_message(data)
