#!/usr/bin/python

from flask import Flask
from flask import request
import threading
import json
import time
import sys, getopt
from paramiko import SSHClient
from paramiko import AutoAddPolicy
from scp import SCPClient
import random
from janus.network.network_driver import JanusNetworkDriver
import threading

lock = threading.Lock()

app = Flask(__name__)

servers_file='servers.json'

SECONDS_TO_EXPIRE = 30
serversi = {}
my_ip=''

def randomMAC():
	mac = [ 0xfe, 0x16, 0x3e,
		random.randint(0x00, 0x7f),
		random.randint(0x00, 0xff),
		random.randint(0x00, 0xff) ]
	return ':'.join(map(lambda x: "%02x" % x, mac))

def vxlan_ip(ip):
        "returns a vxlan ip address"
        return "192.168." + ".".join(ip.split(".")[2:])

def register_port_in_janus(dpid, ip, mac):
        global my_ip
        jd=JanusNetworkDriver(my_ip, 8091)
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

def new_slave_added(new_slave_ip, slave_name):
	global servers
        global my_ip
        #copy local port add to slave
        #copy vxlan add to slave
        #run local port add
        #run vxlan add on new slave toward all servers
        #run vxlan add for new slave on old slaves

        ssh=SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(new_slave_ip, username='ubuntu', password='*******')
        scp = SCPClient(ssh.get_transport())
        print "putting setup files"
        scp.put('setup_br.sh', '~/setup_br.sh')
        scp.put('add_vxlan.sh', '~/add_vxlan.sh')
        scp.close()
        print "setting up bridge and intenal ports"
        stdin, stdout, stderr = ssh.exec_command('~/setup_br.sh br-int tcp:%s:6633 %s' %(my_ip, vxlan_ip(new_slave_ip)))

        stdin.close()
        rets=stdout.readlines()

        p1_mac=rets[0].strip('\n')
        dpid=rets[1].strip('\n')
        print "returned %s" %p1_mac
        register_port_in_janus(dpid, vxlan_ip(new_slave_ip), p1_mac)
        for s,name in servers.iteritems():
            if s == new_slave_ip:
                  continue
            print "setting up vxlan %s -> %s" %(new_slave_ip, s)
            print '~/add_vxlan.sh br-int vxlan-%s %s 10 %s %s' %(s, s, vxlan_ip(s), name)
            ssh.exec_command('~/add_vxlan.sh br-int vxlan-%s %s 10 %s %s' %(s, s, vxlan_ip(s), name))
            time.sleep(1)
        ssh.close()
        with lock:
            for s in servers: 
                if s == new_slave_ip:
                    continue
                try:
                    ssh.connect(s, username='ubuntu', password='*******')
                    print "setting up vxlan %s -> %s" %(s, new_slave_ip)
                    print '~/add_vxlan.sh br-int vxlan-%s %s 10 %s %s' %(new_slave_ip, new_slave_ip, vxlan_ip(new_slave_ip), slave_name)
                    ssh.exec_command('~/add_vxlan.sh br-int vxlan-%s %s 10 %s %s' %(new_slave_ip, new_slave_ip, vxlan_ip(new_slave_ip), slave_name))
                    ssh.close()
                except:
                    print "exception in adding vxlans on otehr servers"
                    pass
        print "new_slave_added successfully"

def read_servers_json_file():
	global servers
	servers = json.loads(open(servers_file).read())
        #servers = {}
	#for srv in s:
	#	servers[srv] = SECONDS_TO_EXPIRE * 3
        print "servers read %s" %servers

def write_json_servers_file():
	global servers
	#s = []
	#for srv in servers:
	#	s.append(srv)
	open(servers_file, 'wt').write(json.dumps(servers))
        print "servers write %s" %servers

@app.route('/add/<slave_name>', methods=['POST'])
def hello_world(slave_name):
        global servers
	worker_ip = request.remote_addr
	if worker_ip not in servers:
		print "new server %s" %worker_ip
                new_slave_added(worker_ip, slave_name)
		servers[worker_ip]=slave_name
		write_json_servers_file()
		#update.update_haproxy(lb_port)
	servers[worker_ip]=slave_name
	return 'Welcome To Pool %s, (i.e., %s)!' %(worker_ip, slave_name)

def timer_thread_func():
        global servers
	while True:
		time.sleep(1)
		remove_server = []
		for server in servers:
                        print 'server %s = %s' %(server, servers[server])
			if servers[server] > 0:
				servers[server] = servers[server] - 1
				if servers[server] == 0:
					remove_server.append(server)
		for srv in remove_server:
			print "server removed %s" %srv
			servers.pop(srv)
		if len(remove_server) > 0:
			write_json_servers_file()
			update.update_haproxy(lb_port)

def main(argv):
        global my_ip
        checkport = 5000
	try:
		opts, args = getopt.getopt(sys.argv[1:],"hi:c:",["myip=","port="])
	except getopt.GetoptError:
		print 'manager.py -i <my ip address> -c <my port=5000>'
		opts = []
                pass
	for opt, arg in opts:
		if opt == '-h':
			print 'manager.py -i <my ip address> -c <my port=5000>'
			sys.exit()
		elif opt in ("-i", "--myip"):
			try:
				my_ip = arg
                        except:
				pass
		elif opt in ("-c", "--port"):
			try:
				checkport = int(arg)
                        except:
				pass
        print "my IP address: %s" %my_ip
        print "my port : %s" %checkport
        if my_ip == '':
                print "my ip is not specified!"
                sys.exit()
	read_servers_json_file()
	#update.update_haproxy(lb_port)
        #t = threading.Thread(target=timer_thread_func)
        #t.daemon = True
        #t.start()
        print "flask starting"
	app.run(host='0.0.0.0', port=checkport)

if __name__ == '__main__':
	main(sys.argv[1:])
