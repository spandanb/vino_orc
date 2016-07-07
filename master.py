"""
Rewrite of manager.py
Does configuration based on static topology.
"""
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
import json 
import argparse
from janus.network.network_driver import JanusNetworkDriver
import time

###########################################
################ Globals ##################
###########################################
my_ip=''

###########################################
################ Utilities ################
###########################################
def vxlan_ip(ip):
        "returns a vxlan ip address"
        return "192.168." + ".".join(ip.split(".")[2:])
        #return "172.16." + ".".join(ip.split(".")[2:])

def read_yaml(filepath):
    """
    Reads the topology in the filepath specified
    """
    import yaml
    with open(filepath) as filedesc:
        return yaml.load(filedesc)

def register_port_in_janus(dpid, ip, mac):
        jd=JanusNetworkDriver('127.0.0.1', 8091)
        network_id_admin='__ADMIN__'
        try:
           jd.createNetwork(network_id_admin)
        except:
           pass
        port=1
        print "register in janus %s, %s, %s" %(dpid, ip, mac)
        try:
           jd.setupPortMacIP(network_id_admin, dpid, mac, ip, port, port_type = 'NORMAL')
        except:
           pass

def write_json_servers_file(servers, servers_file='servers.json'):
    open(servers_file, 'wt').write(json.dumps(servers))
    print "servers write %s" %servers

def read_servers_json_file(servers_file='servers.json'):
    servers = json.loads(open(servers_file).read())
    print "servers read %s" %servers
    return servers

###########################################
#################### Main #################
###########################################
def mesh(nodes_filepath, edges_filepath, servers): 
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    nodes = read_yaml(nodes_filepath)
    edges = read_yaml(edges_filepath)
    #Filter out master node
    nodes = [node for node in nodes if not node['role'] == 'master']

    for node in nodes:
        #Initialize
        ssh.connect(node["ip"], username='ubuntu')
        scp = SCPClient(ssh.get_transport())

        #Update server file    
        servers[node['ip']] = {'name': node['name']}
        write_json_servers_file(servers)

        print "Configuring {}".format(node['ip'])
        scp.put('setup_br.sh', '~/setup_br.sh')
        scp.put('add_vxlan.sh', '~/add_vxlan.sh')
        scp.put('reinit_hosts.sh', '~/reinit_hosts.sh')#Temp fix; remove when image fixed
        if node["role"] == "gateway": 
           scp.put('setup_iptables.sh', '~/setup_iptables.sh')
        else:
           scp.put('setup_gw_routes.sh', '~/setup_gw_routes.sh')
        scp.close()

        print "setting up bridge and internal ports"
        stdin, stdout, stderr = ssh.exec_command('~/setup_br.sh br-int tcp:%s:6633 %s' %(my_ip, vxlan_ip(node["ip"])))
        
        stdin.close()
        rets = stdout.readlines()

        p1_mac = rets[0].strip('\n')
        dpid = rets[1].strip('\n')
        print "returned %s\n" % p1_mac
        register_port_in_janus(dpid, vxlan_ip(node["ip"]), p1_mac)
        ssh.close()
        
    #edges defines a list of pair; we want the body to run for both nodes in pair, i.e.
    #[(node1, node2), ...] -> [(node1, node2), (node2, node1), ...]
    edges.extend(map(lambda pair: (pair[1], pair[0]), edges))
    for node1, node2 in edges:
        #edges only contains the names
        node1 = next(node for node in nodes if node['name'] == node1)
        node2 = next(node for node in nodes if node['name'] == node2)

        ssh.connect(node1["ip"], username='ubuntu')

        print "Configuring {}".format(node1['ip'])
        ssh.exec_command('~/reinit_hosts.sh')
        time.sleep(1)
        print "setting up vxlan %s -> %s" %(node1, node2)
        print '~/add_vxlan.sh br-int vxlan-%s %s 10 %s %s\n' %(node2['ip'], node2['ip'], vxlan_ip(node2['ip']), node2["name"])
        ssh.exec_command('~/add_vxlan.sh br-int vxlan-%s %s 10 %s %s' %(node2["ip"], node2["ip"], vxlan_ip(node2["ip"]), node2["name"]))
        time.sleep(1)

        if node2['role'] == 'gateway' and node1['role'] != 'gateway':
            time.sleep(1)
            print '~/setup_gw_routes.sh %s %s\n' %(vxlan_ip(node1['ip']), vxlan_ip(node2['ip']))
            ssh.exec_command('~/setup_gw_routes.sh %s %s' %(vxlan_ip(node1['ip']), vxlan_ip(node2['ip'])))
            time.sleep(1)

#        #forwards requests on port 80 from gateway to server
#        #Not sure if this is necessary, since HAProxy should do exactly this 
#        if node1["role"] == "gateway" and node2["role"] == "server":
#            #NB: hardcoding the port
#            print '~/setup_iptables.sh %s %s %s\n' %(node1['ip'], vxlan_ip(node2['ip']), '80')
#            ssh.exec_command('~/setup_iptables.sh %s %s %s' %(node1['ip'], vxlan_ip(node2['ip']), '80'))
#            time.sleep(1)

        ssh.close()


def parse_args():
    parser = argparse.ArgumentParser(description='Vino master command line interface')
    parser.add_argument('-i', '--ip-address', required=True, help="My IP address")
    parser.add_argument('-e', '--edges-file', required=True, help="The topology to mesh")
    parser.add_argument('-n', '--nodes-file', required=True, help="The nodes to configure")
    args = parser.parse_args()
    
    global my_ip
    my_ip = args.ip_address

    servers = read_servers_json_file()
    mesh(args.nodes_file, args.edges_file, servers)

if __name__ == "__main__":
    parse_args()
