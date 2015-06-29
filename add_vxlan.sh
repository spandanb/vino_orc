#!/bin/bash

bridge=$1
port_name=$2
remote_addr=$3
vxlan_id=$4
remote_local_ip=$5
remote_name=$6

ofport=`sudo ovs-vsctl get bridge $bridge external_ids:next_of_port | sed s/\"//g `
sudo ovs-vsctl add-port $bridge $port_name -- set interface $port_name type=vxlan options:remote_ip=$remote_addr options:key=$vxlan_id ofport_request=$ofport

ofport=$((ofport+1))
sudo ovs-vsctl set bridge $bridge external_ids:next_of_port=$ofport

sudo bash -c "echo $remote_local_ip $remote_name >> /etc/hosts"
