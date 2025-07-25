import socket
import struct
import time
import os
from datetime import datetime
import sys
import threading
import subprocess


listening_enabled = threading.Event()
listening_enabled.set()  

sys.stdout.reconfigure(line_buffering=True)

containerIp = os.environ[ 'CONT_IP' ]
deviceName = os.environ['DEV_NAME']
fileDestination = os.environ['DESTINATION']

# containerIp = '10.0.52.111'
print('thisIsIP')
print(containerIp)

def create_scanner_packet():
    """Create the scanner-like packet (broadcast)"""
    # This is based on the "scanner to 255" packet you provided
    packet = bytes.fromhex(
        "55 00 00 5a 00 00 00 09 b9 00 a5 2c 0a 00 34 74 "
        "00 00 00 00 4c 6d 33 36 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
        "00 00 00 00"
    )
    return packet

def create_response_packet(scanner_mac, scanner_ip, device_name=deviceName):
    """Create the laptop response packet with dynamic device name
    
    Args:
        scanner_mac: MAC address of the scanner (unused in current implementation)
        scanner_ip: IP address of the scanner (unused in current implementation)
        device_name: Hostname to include in the packet (max 16 chars)
    
    Returns:
        bytes: The complete response packet
    """
    # Get current date/time for the timestamp portion
    now = datetime.now()
    
    # Create the base packet structure
    header = bytes.fromhex(
        "55 00 00 5a 00 00 00 09 b9 00 a5 2c 0a 00 34 74 "
        "00 00 02 c4 4c 6d 33 36 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00"
    )
    
    # Encode and pad the device name (16 bytes total)
    if len(device_name) > 16:
        raise ValueError("Device name must be 16 characters or less")
    name_bytes = device_name.encode('ascii').ljust(16, b'\x00')
    
    footer = bytes.fromhex(
        "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
    )
    
    # Combine all parts
    packet = header + name_bytes + footer
    
    # Replace with current timestamp (bytes 112-118)
    timestamp = struct.pack('<HBBBB', 
                          now.year, 
                          now.month, 
                          now.day, 
                          now.hour, 
                          now.minute)
    packet = packet[:112] + timestamp + packet[118:]
    
    return packet


from receiverProxy import run_sequence

def receive_scan_file(tcp_ip=containerIp, tcp_port=708):

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'/srv/scans/{fileDestination}/scan_{timestamp}.raw'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print(f"Listening for scan data on TCP port {tcp_port}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_sock:
        print(f"Binding TCP socket to {tcp_ip}:{tcp_port}")
        tcp_sock.bind((tcp_ip, tcp_port))
        tcp_sock.listen(1)
        conn, addr = tcp_sock.accept()
        print(f"Scan connection from {addr}")
        with conn, open(output_file, 'wb') as f:
            while True:
                data = conn.recv(4096)
                if not data:
                    print("Scan data transfer complete.")
                    break
                f.write(data)
                print(f"Received {len(data)} bytes")

    print(f"Saved raw scan file as {output_file}")
    listening_enabled.clear()

    # Instead of running conversion script, run the sequence with correct args:
    print("Starting handshake and sending scan file over the network...")

    iface = "eth0"
    src_mac = "bc:24:11:b6:23:f8"
    dst_mac = "80:30:49:e0:c4:0d"
    src_ip = "10.0.52.201"
    dst_ip = "192.168.50.173"
    udp_port = 706
    src_tcp_port = 710
    dst_tcp_port = 708
    packet1_hex = """
    ff ff ff ff ff ff 00 09 b9 00 a5 2c 08 00 45 00
    0010 00 76 00 0a 00 00 40 11 fc fa 0a 00 34 74 0a 00
    0020 34 ff 02 c2 02 c2 00 62 0a 8b 55 00 00 5a 00 00
    0030 00 09 b9 00 a5 2c 0a 00 34 74 00 00 00 00 4c 6d
    0040 33 36 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    0050 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    0060 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    0070 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    0080 00 00 00 00
    """
    packet2_hex = """
    3c 7c 3f 1c 04 24 00 09 b9 00 a5 2c 08 00 45 00
    0010 00 76 00 21 00 00 40 11 fd 78 0a 00 34 74 0a 00
    0020 34 6a 02 c2 02 c2 00 62 b7 1f 55 00 00 5a 54 00
    0030 00 09 b9 00 a5 2c 0a 00 34 74 00 00 00 00 4c 6d
    0040 33 36 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    0050 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    0060 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    0070 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    0080 00 00 00 00
    """
    packet3_hex = """
    3c 7c 3f 1c 04 24 00 09 b9 00 a5 2c 08 00 45 00
    00 2c 00 22 00 00 40 06 fd cc 0a 00 34 74 0a 00
    34 6a 02 c6 02 c4 02 c6 de 77 00 00 00 00 60 02
    05 b4 2e cd 00 00 02 04 05 b4 00 00
    """


    
    # Call your existing function that runs the handshake + sends file
    run_sequence(iface, src_mac, dst_mac, src_ip, dst_ip,
                 udp_port, src_tcp_port, dst_tcp_port,
                 packet1_hex, packet2_hex, packet3_hex,
                 output_file)
    # listening_enabled.set()  

    print("Handshake and file sending completed.")


def can_connect(ip, timeout=2):
    try:
        # '-c 1' → send 1 ping
        # '-W timeout' → wait X seconds for response (Linux-specific)
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if result.returncode == 0:
            print(f"Ping to {ip} succeeded")
            return True
        else:
            print(f"Ping to {ip} failed")
            return False
    except Exception as e:
        print(f"Ping to {ip} failed: {e}")
        return False


receiver_started = False

def main():

    global receiver_started
    # Network configuration
    scanner_ip = "10.0.52.116"  # Scanner broadcast address
    
    can_connect(scanner_ip)

    listen_port = 706            # 0x02C2 in hex
    response_port = 706          # Same port for responses

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Bind to the scanner port
    sock.bind(('0.0.0.0', listen_port))
    print(f"Listening for scanner broadcasts on port {listen_port}...")

    try:
        while True:
            listening_enabled.wait() 
            # Wait for a packet from the scanner
            data, addr = sock.recvfrom(1024)
            print(f"\nReceived packet from {addr}")

            # Check if this is a scanner packet (simple check for the 0x55 header)
            if len(data) >= 4 and data[0] == 0x55 and listening_enabled.is_set():
                print("Valid scanner packet detected")

                # Extract scanner MAC and IP from the packet (positions may need adjustment)
                scanner_mac = data[6:12]  # Adjust positions based on actual packet structure
                scanner_ip = addr[0]      # IP is from the sender

                # Create response packet
                response = create_response_packet(scanner_mac, scanner_ip)

                # Send response back to the scanner
                sock.sendto(response, (scanner_ip, response_port))
                print(f"Sent response to {scanner_ip}:{response_port}")

                print('Starting receive_scan_file() in a separate thread')

                # Start receive_scan_file() in a new thread so it doesn't block
                if not receiver_started:
                    print('Starting receive_scan_file() in a separate thread')
                    threading.Thread(target=receive_scan_file, daemon=True).start()
                    receiver_started = True

                # Hex dump of the response for debugging
                print("Response packet:")
                hexdump(response)
            else:
                print("Unknown packet format, ignoring")

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        sock.close()

def hexdump(data, length=16):
    """Helper function to display hex dumps like in your example"""
    for i in range(0, len(data), length):
        chunk = data[i:i+length]
        hex_str = ' '.join(f"{b:02x}" for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        print(f"{i:04x}   {hex_str.ljust(length*3)} {ascii_str}")

if __name__ == "__main__":
    main()
