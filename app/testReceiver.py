from receiverProxy import modify_packet, parse_hex_dump, send_hex_packet, send_tcp_packet, wait_for_tcp_synack, wait_for_udp_response


iface = "eth0"
src_mac = "bc:24:11:b6:23:f8"
dst_mac = "80:30:49:e0:c4:0d"
src_ip = "172.30.175.74"
dst_ip = "172.30.166.131"
udp_port = 706
src_tcp_port = 710
dst_tcp_port = 708
packet1_hex = """
ff ff ff ff ff ff 00 09 b9 00 a5 2c 08 00 45 00
00 76 00 0a 00 00 40 11 fc fa 0a 00 34 74 0a 00
34 ff 02 c2 02 c2 00 62 0a 8b 55 00 00 5a 00 00
00 09 b9 00 a5 2c 0a 00 34 74 00 00 00 00 4c 6d
33 36 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00
"""
packet2_hex = """
3c 7c 3f 1c 04 24 00 09 b9 00 a5 2c 08 00 45 00
00 76 00 21 00 00 40 11 fd 78 0a 00 34 74 0a 00
34 6a 02 c2 02 c2 00 62 b7 1f 55 00 00 5a 54 00
00 09 b9 00 a5 2c 0a 00 34 74 00 00 00 00 4c 6d
33 36 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00
"""
packet3_hex = """
3c 7c 3f 1c 04 24 00 09 b9 00 a5 2c 08 00 45 00
00 2c 00 22 00 00 40 06 fd cc 0a 00 34 74 0a 00
34 6a 02 c6 02 c4 02 c6 de 77 00 00 00 00 60 02
05 b4 2e cd 00 00 02 04 05 b4 00 00
"""

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

# Call your existing function that runs the handshake + sends file
run_sequence(iface, src_mac, dst_mac, src_ip, dst_ip,
             udp_port, src_tcp_port, dst_tcp_port,
             packet1_hex, packet2_hex, packet3_hex,
             "./scan.raw")