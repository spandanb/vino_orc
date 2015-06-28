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
        self.createIPMap()

    def createIPMap(self):
        "Creates map of host names to hostIP addresses"
        getval = functools.partial(getattr, params)
        hostNames = filter(lambda prop: "host" in prop, dir(params))
        self.IPMap = {} #Map of names to IP addresses
        for name in hostNames:
            key = name.split("_")[1] #host_firewall -> firewall
            self.IPMap[key] = getval(name)
        self.IPList = self.IPMap.values() #List of IP addresses

    def vxlanIP(self, ip):
        "returns a vxlan ip address"
        return "192.168." + ".".join(ip.split(".")[2:])

    def mesh(self):
        """
        Mesh all the hosts together
        """
        #Controller is running on self
        contrIP = utils.get_ip_addr() + ":6633"

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
            self.ssh.exec_command("sudo ifconfig p0 {}/16 up".format(self.vxlanIP(ip)))
            time.sleep(1)
            #Add tunnel endpoints
            for j, other in enumerate(others):
                self.ssh.exec_command("sudo ovs-vsctl add-port br0 vx{} -- set interface vx{} type=vxlan options:remote_ip={} options:key=01"
                    .format(j, j, other))
                time.sleep(1)
            
            self.ssh.close()
    
    def injectDependency(self):
        """
        Inject dependency in /etc/hosts file
        There are two dependencies:
            1)GW -> WP
            2)WP -> DB
        """
        self.ssh.connect(self.IPMap["gateway"], username=params.username, password=params.password)
        self.ssh.exec_command('sudo echo "wordpress {}" | sudo tee -a /etc/hosts'.format(self.vxlanIP(self.IPMap["wordpress"]))) 
        self.ssh.close()

        self.ssh.connect(self.IPMap["wordpress"], username=params.username, password=params.password)
        self.ssh.exec_command('sudo echo "database {}" | sudo tee -a /etc/hosts'.format(self.vxlanIP(self.IPMap["database"]))) 
        self.ssh.close()

    def runHAProxy(self):
        self.ssh.connect(self.IPMap["gateway"], username=params.username, password=params.password)
        cmd = "sed -i '6i server srv1 {}:80' /home/ubuntu/haproxy.cfg".format(self.vxlanIP(self.IPMap['wordpress']))
        self.ssh.exec_command(cmd) 
        time.sleep(1)
        self.ssh.exec_command("haproxy -f /home/ubuntu/haproxy.cfg")
        self.ssh.close()

if __name__ == "__main__":
    vinod = Vinod()
    vinod.mesh()
    vinod.injectDependency()
    vinod.runHAProxy()
