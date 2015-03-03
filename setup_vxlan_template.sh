#!/usr/bin/bash

#Create VXLAN Tunnel between 2 hosts

sudo ovs-vsctl add-br br0
sudo ovs-vsctl add-port br0 p0 -- set interface p0 type=internal

sudo ovs-vsctl add-port br0 p0 -- set interface p0 type=internal
mac_addr=`sudo ovs-vsctl get interface p0 mac_in_use`
sudo ovs-vsctl set interface p0 mac=$$mac_addr
sudo ifconfig p0 $VXLAN_IP up

sudo ovs-vsctl add-port br0 vxlan0 -- set interface vxlan0 type=vxlan options:remote_ip=$REMOTE_IP options:keys=01
