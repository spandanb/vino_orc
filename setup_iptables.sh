#!/bin/bash

#Creates iptables rule for forwarding from $MY_IP:$port to $target:$port

MY_IP=$1
target=$2
port=$3
#Enables forwarding
sudo bash -c "echo 1 > /proc/sys/net/ipv4/ip_forward"
# -t nat -A PREROUTING:  act on the nat table during PREROUTING, ie. effects packets as soon as they come in
# -d : destination
# -p : protocol
# -m : match on some property, tcp
# --dport: destination port
# -j : specifies target of the rule
# DNAT: destination NAT
# --to-destination
sudo iptables -t nat -A PREROUTING -d $MY_IP/32 -p tcp -m tcp --dport $port -j DNAT --to-destination $target:$port
