#!/bin/bash

# Drop RST packets sent from Scapy-handled TCP connections
echo "Applying iptables rule to drop TCP RSTs..."
iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP

# Run your application
exec "$@"
