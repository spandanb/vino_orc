"""
Vinod - Centralized version of vino

Execute the following on each host

sudo ovs-vsctl add-br br0
sudo ovs-vsctl set-controller br0 tcp:$CONTR_ADDR
sudo ovs-vsct set-fail-mode br0 secure
sudo ovs-vsctl set controller br0 connection-mode=out-of-band

#Add internal port
sudo ovs-vsctl add-port br0 p0 -- set interface p0 type=internal

mac_addr=`sudo ovs-vsctl get interface p0 mac_in_use`
sudo ovs-vsctl set interface p0 mac=$$mac_addr
sudo ifconfig p0 $VXLAN_IP/24 up

sudo ovs-vsctl add-port br0 vx0 -- set interface vx0 type=vxlan options:remote_ip=$remote_ip options:key=01
"""
import paramiko as pr
import subprocess as sp
import functools
import time
import pdb

import utils
import params


class Vinod(object):
    def __init__(self):
        self.ssh = pr.SSHClient()
        self.ssh.set_missing_host_key_policy(pr.AutoAddPolicy())
        self.getIPs()

    def getIPs(self):    
        """Get all the host IP addresses"""
        getval = functools.partial(getattr, params)
        self.IPList = map(getval, filter(lambda prop: "host" in prop, dir(params)))
        #self.IPList = ["10.12.1.68", "10.12.1.67"]

    def vxlan(self, ip):
        "returns a vxlan ip address"
        return "192.168." + ".".join(ip.split(".")[2:])

    def mesh(self):
        """
        Mesh all the hosts together
        """
        #Controller is running on self
        contrIP = utils.get_ip_addr()

        for i, ip in enumerate(self.IPList): 
            
            print "configuring host with IP: {}".format(ip)
            #list of other IP addresses
            others = self.IPList[:i] + self.IPList[i+1:]
            
            self.ssh.connect(ip, username=params.username, password=params.password)
            self.ssh.exec_command("sudo ovs-vsctl del-br br0") #Cleanup
            time.sleep(1)
            #Add bridge, setup controller
            self.ssh.exec_command("sudo ovs-vsctl add-br br0")
            time.sleep(1)
            self.ssh.exec_command("sudo ovs-vsctl set-controller br0 tcp:{}".format(contrIP))
            time.sleep(1)
            self.ssh.exec_command("sudo ovs-vsct set-fail-mode br0 secure")
            time.sleep(1)
            self.ssh.exec_command("sudo ovs-vsctl set controller br0 connection-mode=out-of-band")
            time.sleep(1)
            #Add virtual port
            self.ssh.exec_command("sudo ovs-vsctl add-port br0 p0 -- set interface p0 type=internal")
            time.sleep(1)
            stdin, stdout, stderr = self.ssh.exec_command("sudo ovs-vsctl get interface p0 mac_in_use")
            time.sleep(1)
            self.ssh.exec_command("sudo ovs-vsctl set interface p0 mac={}".format(stdin))
            time.sleep(1)
            self.ssh.exec_command("sudo ifconfig p0 {}/24 up".format(self.vxlan(ip)))
            time.sleep(1)
            #Add tunnel endpoints
            for j, other in enumerate(others):
                self.ssh.exec_command("sudo ovs-vsctl add-port br0 vx{} -- set interface vx{} type=vxlan options:remote_ip={} options:key=01"
                    .format(j, j, other))
                time.sleep(1)
            
            self.ssh.close()

vinod = Vinod()
vinod.mesh()
