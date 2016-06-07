#!/bin/bash

src_ip=$1
gw_ip=$2

sudo bash -c "echo 200 isp2 >> /etc/iproute2/rt_tables"
#ip rule add: Add a new rule
#from $src_ip: match on src prefix 
#table isp2: if previous matched, do lookup in 'isp2' table
sudo ip rule add from $src_ip table isp2
#add default route for device p1
sudo ip route add default via $gw_ip dev p1 table isp2

