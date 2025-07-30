from src.receiver_proxy import run_sequence
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
             "./scan.raw")