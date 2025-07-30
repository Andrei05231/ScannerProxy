from pydantic import BaseModel, Field
from typing import Literal
import struct

class ScannerMessage(BaseModel):
    model: str = Field(..., min_length=1, max_length=4)
    scan_length: int
    copies: int
    scan_pc: int
    ip: str = "192.168.1.137"
    hostname: str = "DESKTOP-AS2MOOV"
    firmware_version: str = "2.5.2"
    year: int = 2025
    day_of_year: int = 1822
    hour: int = 3
    minute: int = 12
    second: int = 26
    second_alt: int = 57

    def to_bytes(self) -> bytes:
        header = b'\x55\x00\x00\x5a\x00\x00\x00\x09\xb9\x00\x2c\x84'

        # Convert IP to bytes
        ip_parts = bytes(map(int, self.ip.split(".")))
        unknown1 = b'\x00\x00\x02\xc4'

        # Model and hostname to fixed-length fields
        model_bytes = self.model.encode("ascii").ljust(40, b'\x00')
        hostname_bytes = self.hostname.encode("ascii").ljust(40, b'\x00')

        # Date/time section
        datetime_bytes = struct.pack(
            '<H H B B B B',
            self.year,
            self.day_of_year,
            self.hour,
            self.minute,
            self.second,
            self.second_alt
        )

        # Scan stats
        scan_info = struct.pack('<H B H', self.scan_length, self.copies, self.scan_pc)

        return (
            header +
            ip_parts +
            unknown1 +
            model_bytes +
            hostname_bytes +
            scan_info +
            datetime_bytes +
            b'\x00\x00'  # footer or terminator
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "ScannerMessage":
        # Parse known offsets based on structure
        model = data[20:60].rstrip(b'\x00').decode('ascii')
        scan_length = struct.unpack_from('<H', data, 100)[0]
        copies = data[102]
        scan_pc = struct.unpack_from('<H', data, 103)[0]
        year, day, hour, minute, second, second_alt = struct.unpack_from('<H H B B B B', data, 105)

        return cls(
            model=model,
            scan_length=scan_length,
            copies=copies,
            scan_pc=scan_pc,
            year=year,
            day_of_year=day,
            hour=hour,
            minute=minute,
            second=second,
            second_alt=second_alt
        )


# Example usage
msg = ScannerMessage(
    model="L24e",
    scan_length=11863,
    copies=1,
    scan_pc=6044
)
packet = msg.to_bytes()
print(packet.hex(" "))
