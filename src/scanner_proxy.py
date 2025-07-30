import socket
import struct
import threading
from datetime import datetime

# === CONFIGURATION ===
SCANNER_SUBNET = "10.0.52."
SCANNER_PORT = 706
RECEIVER_IP = "192.168.50.173"
RECEIVER_PORT = 706
RECEIVER_TCP_PORT = 708
LOCAL_TCP_PORT = 708

scanner_udp_addr = None  # ('ip', port)

def create_response_packet(scanner_mac, scanner_ip, device_name="Custom-Scan"):
    now = datetime.now()
    header = bytes.fromhex(
        "55 00 00 5a 00 00 00 09 b9 00 a5 2c 0a 00 34 74 "
        "00 00 02 c4 4c 6d 33 36 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00"
    )
    name_bytes = device_name.encode('ascii').ljust(16, b'\x00')
    footer = bytes.fromhex("00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00")
    packet = header + name_bytes + footer
    timestamp = struct.pack('<HBBBB', now.year, now.month, now.day, now.hour, now.minute)
    return packet[:112] + timestamp + packet[118:]

def fake_scanner_discovery():
    # Minimal fake discovery packet based on original
    return bytes.fromhex(
        "55 00 00 5a 00 00 00 09 b9 00 a5 2c 0a 00 34 74 "
        "00 00 00 00 4c 6d 33 36 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
        "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
        "00 00 00 00"
    )

def udp_proxy():
    global scanner_udp_addr

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_sock.bind(('0.0.0.0', SCANNER_PORT))
    print(f"[UDP] Proxy listening on port {SCANNER_PORT}")

    while True:
        data, addr = udp_sock.recvfrom(2048)
        src_ip, _ = addr

        if src_ip.startswith(SCANNER_SUBNET):
            # From scanner
            print(f"[UDP] Received handshake from scanner at {addr}")
            scanner_udp_addr = addr

            # Step 1: Impersonate scanner → send fake discovery to receiver
            udp_sock.sendto(data, (RECEIVER_IP, RECEIVER_PORT))
            print(f"[UDP] Sent fake discovery to receiver at {RECEIVER_IP}:{RECEIVER_PORT}")

            # Step 2: Wait briefly for receiver's response
            udp_sock.settimeout(1.0)
            try:
                reply, receiver_addr = udp_sock.recvfrom(2048)
                if receiver_addr[0] == RECEIVER_IP:
                    # Forward receiver's reply to scanner
                    udp_sock.sendto(reply, scanner_udp_addr)
                    print(f"[UDP] Forwarded receiver reply to scanner at {scanner_udp_addr}")
            except socket.timeout:
                print("[UDP] No reply from receiver (timeout)")

            udp_sock.settimeout(None)

            # Step 3: Send our own response packet to scanner
            scanner_mac = data[6:12]
            scanner_ip = scanner_udp_addr[0]
            response = create_response_packet(scanner_mac, scanner_ip)
            udp_sock.sendto(response, scanner_udp_addr)
            print(f"[UDP] Sent custom response to scanner at {scanner_udp_addr}")

        else:
            print(f"[UDP] Ignoring packet from non-scanner source: {addr}")

def forward_tcp_data(scanner_conn, receiver_ip, receiver_port):
    try:
        receiver_conn = socket.create_connection((receiver_ip, receiver_port))
        print(f"[TCP] Connected to receiver at {receiver_ip}:{receiver_port}")

        def pipe(src, dst, label):
            try:
                while True:
                    data = src.recv(4096)
                    if not data:
                        break
                    dst.sendall(data)
                    print(f"[TCP] {label} {len(data)} bytes")
            except Exception as e:
                print(f"[TCP] {label} error: {e}")
            finally:
                try: dst.shutdown(socket.SHUT_WR)
                except: pass

        # Bi-directional pipe
        t1 = threading.Thread(target=pipe, args=(scanner_conn, receiver_conn, "Scanner → Receiver"), daemon=True)
        t2 = threading.Thread(target=pipe, args=(receiver_conn, scanner_conn, "Receiver → Scanner"), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    except Exception as e:
        print(f"[TCP] Error connecting to receiver: {e}")
    finally:
        try: scanner_conn.close()
        except: pass
        try: receiver_conn.close()
        except: pass
        print("[TCP] TCP session closed")

def tcp_proxy():
    print(f"[TCP] Listening for scanner TCP connection on port {LOCAL_TCP_PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('0.0.0.0', LOCAL_TCP_PORT))
        server_sock.listen(5)
        while True:
            conn, addr = server_sock.accept()
            print(f"[TCP] Accepted connection from scanner at {addr}")
            threading.Thread(
                target=forward_tcp_data,
                args=(conn, RECEIVER_IP, RECEIVER_TCP_PORT),
                daemon=True
            ).start()

def main():
    threading.Thread(target=udp_proxy, daemon=True).start()
    tcp_proxy()

if __name__ == "__main__":
    main()
