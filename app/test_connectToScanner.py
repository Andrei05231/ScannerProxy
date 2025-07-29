import socket
import time

# Configuration (should match connectToScanner.py)
scanner_ip = "172.30.166.131"  # IP of the service container
listen_port = 706
response_port = 706


# Example scanner packets (should match expected format)
packet1_hex = """
55 00 00 5a 00 00 00 09 b9 00 a5 2c 0a 00 34 74
00 00 00 00 4c 6d 33 36 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
00 00 00 00 00 00 00 00 00 00
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

    # Send first scanner packet
    packet_bytes1 = parse_hex_dump(packet1_hex)
    print(f"Sending first scanner packet to {scanner_ip}:{listen_port}...")
    sock.sendto(packet_bytes1, (scanner_ip, listen_port))

    # Wait for first response
    try:
        resp1, addr1 = sock.recvfrom(1024)
        print(f"Received response to first packet from {addr1}: {resp1.hex()}")
    except socket.timeout:
        print("No response received from service to first packet.")
        sock.close()
        exit(1)
