#!/usr/bin/bash

#Set of utility functions

#Functions
#======================================

setup_ovs()
{
    #Sets up OVS- creates bridge and adds port
    #Arguments: $1- $VXLAN_IP is the assigned ip address of this host
    
    sudo ovs-vsctl add-br br0
    sudo ovs-vsctl add-port br0 p0 -- set interface p0 type=internal
    
    mac_addr=`sudo ovs-vsctl get interface p0 mac_in_use`
    sudo ovs-vsctl set interface p0 mac=$$mac_addr
    sudo ifconfig p0 $$VXLAN_IP up
}

create_vxlan_tunnel()
{
    #Create VXLAN Tunnel between 2 hosts
    #Arguments: $1- remote host's internal IP address
    #   i.e. the non-vxlan ip of the remote host
    sudo ovs-vsctl add-port br0 vxlan0 -- set interface vxlan0 type=vxlan options:remote_ip=$1 options:keys=01
}

run_vino_slave()
{
    #Creates screens and runs vino_slave in it
    #Creates screen named 'my_screen', with tab named 'shell' that runs bash
    screen -d -m -S my_screen -t shell -s bash
    sleep 2
    #Similar to above, creates tab named my_screen_tab
    screen -S my_screen -X screen -t my_screen_tab
    sleep 2
    #Stuff the cd command and press 'enter'
    screen -S my_screen -p my_screen_tab -X stuff 'cd /home/ubuntu/vino_orc'`echo -ne '\015'`
    sleep 2
    #Run vino slave
    screen -S my_screen -p my_screen_tab -X stuff 'python vino_slave.py'`echo -ne '\015'`
    sleep 2
    screen -r my_screen -X hardstatus alwayslastline '%{= .} %-Lw%{= .}%> %n%f %t*%{= .}%+Lw%< %-=%{g}(%{d}%H/%l%{g})'
}

#Processing Logic
#======================================
echo "Calling vino.sh with arguments: "
for var in "$@"
do
    echo "$var"
done

case "$1" in
    setup_ovs|ovs)
        #Call setup_ovs with overlay IP Address
        setup_ovs $2
        ;;
    create_vxlan_tunnel|vxlan)
        create_vxlan_tunnel $2
        ;;
    run_vino_slave|slave)
        run_vino_slave
        ;;
    *)
        echo "Invalid argument"
esac
