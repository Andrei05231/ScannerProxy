from scapy.all import *
import re
import time

def parse_hex_dump(hex_string):
    lines = hex_string.strip().splitlines()
    cleaned_lines = []
    for line in lines:
        # Remove line number offset at start
        line = re.sub(r"^\s*[0-9a-fA-F]{4,5}\s*", "", line)
        cleaned_lines.append(line)
    joined = " ".join(cleaned_lines)
    hex_bytes = re.findall(r'[0-9a-fA-F]{2}', joined)
    return bytes.fromhex(''.join(hex_bytes))

def modify_packet(raw_bytes, src_mac, dst_mac, src_ip, dst_ip):
    pkt = Ether(raw_bytes)
    pkt.src = src_mac
    pkt.dst = dst_mac
    if IP in pkt:
        pkt[IP].src = src_ip
        pkt[IP].dst = dst_ip
        del pkt[IP].chksum
    if UDP in pkt:
        del pkt[UDP].chksum
        del pkt[UDP].len
    pkt = pkt.__class__(raw(pkt))
    return pkt

def send_hex_packet(hex_string, iface, src_mac, dst_mac, src_ip, dst_ip):
    raw_bytes = parse_hex_dump(hex_string)
    pkt = modify_packet(raw_bytes, src_mac, dst_mac, src_ip, dst_ip)
    send(pkt[IP], iface=iface, verbose=False)
    print("Packet sent.")

def wait_for_udp_response(iface, src_ip, dst_ip, udp_port, timeout=30):
    print(f"Waiting for UDP response from {dst_ip} on port {udp_port}...")
    def stop_filter(pkt):
        return (UDP in pkt and
                pkt[UDP].sport == udp_port and
                pkt[IP].src == dst_ip and
                pkt[IP].dst == src_ip)
    pkts = sniff(iface=iface, filter=f"udp and src host {dst_ip} and src port {udp_port} and dst port {udp_port}",
                timeout=timeout, stop_filter=stop_filter)
    if pkts:
        print(f"Received response from {dst_ip}")
        return True
    else:
        print("No response received")
        return False

def wait_for_tcp_synack(iface, src_ip, dst_ip, src_port, dst_port, timeout=10):
    print("Waiting for TCP SYN+ACK...")
    def stop_filter(pkt):
        if (TCP in pkt and pkt[TCP].flags == "SA" and
            pkt[IP].src == dst_ip and pkt[IP].dst == src_ip and
            pkt[TCP].sport == dst_port and pkt[TCP].dport == src_port):
            return True
        return False
    pkts = sniff(iface=iface, filter=f"tcp and src host {dst_ip} and dst host {src_ip} and src port {dst_port} and dst port {src_port}",
                 timeout=timeout, stop_filter=stop_filter)
    if pkts:
        print("Received TCP SYN+ACK")
        return pkts[0]
    else:
        print("No TCP SYN+ACK received.")
        return None

def send_tcp_packet(pkt, iface):
    send(pkt[IP], iface=iface, verbose=False)
    print("TCP packet sent.")

def run_sequence(iface, src_mac, dst_mac, src_ip, dst_ip,
                 udp_port, src_tcp_port, dst_tcp_port,
                 packet1_hex, packet2_hex, packet3_hex, file_to_send):

    # Send first UDP packet
    print("Sending first UDP packet...")
    send_hex_packet(packet1_hex, iface, src_mac, dst_mac, src_ip, dst_ip)

    # Wait for UDP response
    if not wait_for_udp_response(iface, src_ip, dst_ip, udp_port):
        print("Did not receive UDP response, aborting.")
        return

    # Send second UDP packet
    print("Sending second UDP packet...")
    send_hex_packet(packet2_hex, iface, src_mac, dst_mac, src_ip, dst_ip)

    # Wait for UDP response again
    if not wait_for_udp_response(iface, src_ip, dst_ip, udp_port):
        print("Did not receive UDP response after second packet, aborting.")
        return

    # Send third TCP packet (SYN)
    print("Starting TCP handshake with SYN packet...")
    raw_bytes = parse_hex_dump(packet3_hex)
    tcp_syn_pkt = modify_packet(raw_bytes, src_mac, dst_mac, src_ip, dst_ip)

    # Make sure TCP ports match passed arguments
    tcp_syn_pkt[TCP].sport = src_tcp_port
    tcp_syn_pkt[TCP].dport = dst_tcp_port
    del tcp_syn_pkt[TCP].chksum
    del tcp_syn_pkt[IP].chksum
    tcp_syn_pkt = tcp_syn_pkt.__class__(raw(tcp_syn_pkt))

    send_tcp_packet(tcp_syn_pkt, iface)

    # Wait for SYN+ACK
    synack_pkt = wait_for_tcp_synack(iface, src_ip, dst_ip, src_tcp_port, dst_tcp_port)
    if not synack_pkt:
        print("TCP handshake failed, aborting.")
        return

    # Send ACK to complete handshake
    tcp_ack_pkt = Ether(src=src_mac, dst=dst_mac)/\
                  IP(src=src_ip, dst=dst_ip)/\
                  TCP(sport=src_tcp_port, dport=dst_tcp_port,
                      flags='A',
                      seq=synack_pkt[TCP].ack,
                      ack=synack_pkt[TCP].seq + 1)
    send_tcp_packet(tcp_ack_pkt, iface)

    # Open file and send contents over TCP (raw)
    print(f"Sending file {file_to_send} over TCP...")
    with open(file_to_send, 'rb') as f:
        data = f.read()

    # Send data in batches of 1460 bytes (typical MSS)
    MSS = 1460
    seq = tcp_ack_pkt[TCP].seq
    ack = tcp_ack_pkt[TCP].ack
    for i in range(0, len(data), MSS):
        chunk = data[i:i+MSS]
        pkt = Ether(src=src_mac, dst=dst_mac)/\
              IP(src=src_ip, dst=dst_ip)/\
              TCP(sport=src_tcp_port, dport=dst_tcp_port,
                  flags='PA',
                  seq=seq,
                  ack=ack)/\
              Raw(load=chunk)
        del pkt[TCP].chksum
        del pkt[IP].chksum
        pkt = pkt.__class__(raw(pkt))
        send_tcp_packet(pkt, iface)
        seq += len(chunk)

    print("File sent.")

    # Close TCP connection (FIN handshake)
    fin_pkt = Ether(src=src_mac, dst=dst_mac)/\
              IP(src=src_ip, dst=dst_ip)/\
              TCP(sport=src_tcp_port, dport=dst_tcp_port,
                  flags='FA',
                  seq=seq,
                  ack=ack)
    del fin_pkt[TCP].chksum
    del fin_pkt[IP].chksum
    fin_pkt = fin_pkt.__class__(raw(fin_pkt))
    send_tcp_packet(fin_pkt, iface)
    print("Sent FIN to close connection.")

if __name__ == "__main__":
    print("This module is designed to be imported and called from another script.")