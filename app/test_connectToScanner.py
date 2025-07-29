import socket
import time

# Configuration (should match connectToScanner.py)
scanner_ip = "172.30.166.131"  # IP of the service container
listen_port = 706
response_port = 706

# Example scanner packet (should match expected format)
packet1_hex = """
55 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
"""

def parse_hex_dump(hex_string):
    lines = hex_string.strip().splitlines()
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            # Remove line number offset if present
            line = line.split(' ', 1)[-1] if line[:4].isdigit() else line
            cleaned_lines.append(line)
    joined = " ".join(cleaned_lines)
    hex_bytes = joined.replace(' ', '')
    return bytes.fromhex(hex_bytes)

if __name__ == "__main__":
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(5)
    local_ip = "172.30.175.74"  # IP of the test client
    sock.bind((local_ip, listen_port))

    # Send scanner packet
    packet_bytes = parse_hex_dump(packet1_hex)
    print(f"Sending scanner packet to {scanner_ip}:{listen_port}...")
    sock.sendto(packet_bytes, (scanner_ip, listen_port))

    # Wait for response
    try:
        resp, addr = sock.recvfrom(1024)
        print(f"Received response from {addr}: {resp.hex()}")
    except socket.timeout:
        print("No response received from service.")
    finally:
        sock.close()
