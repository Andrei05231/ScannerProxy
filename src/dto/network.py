from pydantic import BaseModel, Field
from typing import ClassVar
from ipaddress import IPv4Address, AddressValueError
import socket


class ScannerProtocolMessage(BaseModel):
    SIGNATURE: ClassVar[bytes] = b'\x55\x00\x00'
    TYPE_OF_REQUEST: ClassVar[bytes] = b'\x5a\x00\x00'

    signature: bytes = Field(default=SIGNATURE)
    type_of_request: bytes = Field(default=TYPE_OF_REQUEST)
    reserved1: bytes = Field(default=b'\x00' * 6)  # 6 bytes reserved
    initiator_ip: IPv4Address = Field(default=IPv4Address("192.168.1.137"))
    reserved2: bytes = Field(default=b'\x00\x00\x00\x00')
    src_name: bytes = Field(default=b"L24e")
    dst_name: bytes = Field(default=b"")
    reserved3: bytes = Field(default=b'\x00' * 10)  # May contain timestamp

    def to_bytes(self) -> bytes:
        ip_bytes = self.initiator_ip.packed  # Convert IPv4Address to 4 bytes
        src_bytes = self.src_name.ljust(20, b'\x00')
        dst_bytes = self.dst_name.ljust(40, b'\x00')
        return (
            self.signature +
            self.type_of_request +
            self.reserved1 +
            ip_bytes +
            self.reserved2 +
            src_bytes +
            dst_bytes +
            self.reserved3
        )
    
    def dbg(self):
        print(f"Signature: {len(self.signature)} {self.signature.hex()}")
        print(f"Type of Request: {len(self.type_of_request)} {self.type_of_request.hex()}")
        print(f"Reserved1: {len(self.reserved1)} {self.reserved1.hex()}")
        print(f"Initiator IP: {self.initiator_ip} (4 bytes: {self.initiator_ip.packed.hex()})")
        print(f"Reserved2: {len(self.reserved2)} {self.reserved2.hex()}")
        print(f"Source Name: {len(self.src_name)} {self.src_name.hex()}")
        print(f"Destination Name: {len(self.dst_name)} {self.dst_name.hex()}")
        print(f"Reserved3: {len(self.reserved3)} {self.reserved3.hex()}")

    @classmethod
    def from_bytes(cls, data: bytes) -> "ScannerProtocolMessage":
        if len(data) != 90:
            raise ValueError(f"Expected 90 bytes, got {len(data)}")

        signature = data[0:3]
        type_of_request = data[3:6]
        reserved1 = data[6:12]
        ip_bytes = data[12:16]
        initiator_ip = IPv4Address(ip_bytes)  # Create IPv4Address directly from 4 bytes
        reserved2 = data[16:20]
        src_name = data[20:40].rstrip(b'\x00')
        dst_name = data[40:80].rstrip(b'\x00')
        reserved3 = data[80:90]

        return cls(
            signature=signature,
            type_of_request=type_of_request,
            reserved1=reserved1,
            initiator_ip=initiator_ip,
            reserved2=reserved2,
            src_name=src_name,
            dst_name=dst_name,
            reserved3=reserved3
        )
