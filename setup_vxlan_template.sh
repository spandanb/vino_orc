#!/bin/bash

#Create VXLAN Tunnel between 2 hosts
#This is a template file
#$$VXLAN_IP is the assigned ip address of this host
#$$REMOTE_IP is the internal (non-vxlan ip of the remote host)
#$$CONTR_ADDR is the <ip_addr>:<port> of the controller
#$$INTERNAL_IP is the vxlan ip of this bridge

#Create bridge named br0
sudo ovs-vsctl add-br br0

#Set and configure controller for br0
sudo ovs-vsctl set-controller br0 tcp:$CONTR_ADDR
ssudo ovs-vsct set-fail-mode br0 secure
sudo ovs-vsctl set controller br0 connection-mode=out-of-band

#Add internal port
sudo ovs-vsctl add-port br0 p0 -- set interface p0 type=internal

mac_addr=`sudo ovs-vsctl get interface p0 mac_in_use`
sudo ovs-vsctl set interface p0 mac=$$mac_addr
sudo ifconfig p0 $VXLAN_IP/24 up

#Add virtual port
sudo ovs-vsctl add-port br0 vxlan0
