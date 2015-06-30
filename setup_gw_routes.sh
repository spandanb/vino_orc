#!/bin/bash

src_ip=$1
gw_ip=$2

sudo bash -c "echo 200 isp2 >> /etc/iproute2/rt_tables"
sudo ip rule add from $src_ip table isp2
sudo ip route add default via $gw_ip dev p1 table isp2

