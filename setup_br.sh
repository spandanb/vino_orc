#!/bin/bash

bridge=$1
controller=$2
local_ip=$3

sudo ovs-vsctl -- --if-exists del-br $bridge

sudo ovs-vsctl -- --may-exist add-br $bridge
sudo ovs-vsctl set-controller $bridge $controller
sudo ovs-vsctl set bridge $bridge protocols=OpenFlow10
sudo ovs-vsctl set-fail-mode $bridge secure
sudo ovs-vsctl set controller $bridge connection-mode="out-of-band"

for port in p1 p2 p3; do
   sudo ovs-vsctl -- --may-exist add-port $bridge $port -- set interface $port type=internal
   sudo ovs-vsctl set interface $port mac=`sudo ovs-vsctl get interface $port mac_in_use`
done

sudo ovs-vsctl set bridge $bridge external_ids:next_of_port=10

sudo ifconfig p1 $local_ip/16 up
sudo ifconfig p1 mtu 1400 up
sudo ifconfig p2 up promisc
sudo ifconfig p3 up promisc
sudo ovs-vsctl get interface p1 mac | sed s/\"//g
sudo ovs-vsctl get bridge $bridge datapath_id | sed s/\"//g
