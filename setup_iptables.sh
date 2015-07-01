#!/bin/bash

MY_IP=$1
target=$2
port=$3
sudo bash -c "echo 1 > /proc/sys/net/ipv4/ip_forward"
sudo iptables -t nat -A PREROUTING -d $MY_IP/32 -p tcp -m tcp --dport $port -j DNAT --to-destination $target:$port
