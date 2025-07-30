import socket

from src.dto.network import ScannerProtocolMessage

LOCAL_IP = "192.168.1.139"
SERVER_IP = "192.168.1.138"
BROADCAST_IP = "192.168.1.255"
#SERVER_IP = "172.30.166.131"
UDP_PORT = 706
TCP_DST_PORT = 708

UDP_PAYLOAD = """
55 00 00 5a 54 00 00 09 b9 00 a5 2c 0a 00 34 74
00 00 00 00 4c 6d 33 36 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00
"""

if __name__ == "__main__":

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting
    sock.settimeout(5)
    sock.bind((LOCAL_IP, UDP_PORT))

    # Initialize Discovery

    x = ScannerProtocolMessage()
    x.debug()

    #udp_packet_bytes = bytes.fromhex(UDP_PAYLOAD)
    udp_packet_bytes = x.to_bytes()
    print(len(udp_packet_bytes))
    print(f"Sending UDP scanner packet to {SERVER_IP}:{UDP_PORT}...")
    sock.sendto(udp_packet_bytes, (BROADCAST_IP, UDP_PORT))

    try:
        resp, addr = sock.recvfrom(1024)
        y = ScannerProtocolMessage.from_bytes(resp)
        y.debug()
        print(f"Received response to first packet from {addr}: {y}")
        # print(f"Received response to first packet from {addr}: {resp.hex()}")
    except socket.timeout:
        print("No response received from service to first packet.")
        sock.close()
        exit(1)

