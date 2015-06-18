import pika
from cPickle import loads
from utils import get_ip_addr
import sys
import subprocess as sp
from string import Template
import pdb

class VinoSlave(object):
    def __init__(self):
        ip_addr = "10.12.1.53" #Master
        port = 5672 
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters=pika.ConnectionParameters(ip_addr, port, '/', credentials)
        
        #Sometimes initial connection does not work
        while True:
            try:
                connection = pika.BlockingConnection(parameters)
                break
            except pika.exceptions.AMQPConnectionError:
                pass
            
        self.channel = connection.channel()
    
        #configire for receive
        self.channel.queue_declare(queue='hello')
    
        #configure for send
        self.channel.exchange_declare(exchange='bcast', type='fanout')
    
        result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        
        self.channel.queue_bind(exchange='bcast',
                           queue=queue_name)
        
        #This configures consume function 
        self.channel.basic_consume(self.callback,
                              queue=queue_name,
                              no_ack=True)

        self.contr_addr = "10.12.11.34:6633"
        self.ip_addr = get_ip_addr()
        self.slaves = {}

    def diff(self, new, old):
        #Gives new ip address in new [list]
        old_keys = old.keys()
        for key in new.keys():
            if key not in old_keys:
                return key

    def setup_vxlan(self, subs, outfile="setup_vxlan.sh",
                template="setup_vxlan_template.sh"):
        
        infile = open(template)
        src = Template( infile.read() )
        result = src.substitute(subs)
        infile.close()
        
        ofile = open(outfile, 'w')
        ofile.write(result)
        ofile.close()
        sp.call(["bash", "./" + outfile])
    
    def create_tunnel(self, new_ip):
        """
        Create tunnel with new_ip
        """
        #cmd = "sudo ovs-vsctl add-port br0 vxlan0 -- set interface vxlan0 type=vxlan options:remote_ip={} options:keys=01"
        cmd = "sudo ovs-vsctl set interface vxlan0 type=vxlan options:remote_ip={} options:key=01"
        sp.call(cmd.format(new_ip).split())
            
    def create_tunnels_init(self):
        """
        Multi host version of ^
        Create tunnels with all existing hosts
        """
        #cmd = "sudo ovs-vsctl add-port br0 vxlan0"
        #sp.call(cmd.format(ip_addr).split())

        cmd = "sudo ovs-vsctl set interface vxlan0 type=vxlan options:remote_ip={} options:key=01"
        remote_ips = self.slaves.keys()
        remote_ips.remove(self.ip_addr)
        for ip_addr in remote_ips:
            sp.call(cmd.format(ip_addr).split())

    def callback(self, ch, method, properties, body):
        """
        callback for something received 
        """
        new_slaves = loads(body)
        print " [x] %r" % (new_slaves,)

        #New init
        if not self.slaves:
            print " [x] Initializing mesh"
            self.vxlan_ip = new_slaves[self.ip_addr]
            #Substitution dictionary
            subs = {'VXLAN_IP': self.vxlan_ip, 'CONTR_ADDR':self.contr_addr} 
            self.setup_vxlan(subs)
            self.slaves = new_slaves
            self.create_tunnels_init()
            
        else:
            new_ip = self.diff(new_slaves, self.slaves)
            print " [x] New Slave is {}".format((new_ip, new_slaves[new_ip]))
            self.create_tunnel(new_ip)
            self.slaves = new_slaves


    def hello(self):
        """
        Send initial message
        """
        message = self.ip_addr 
        self.channel.basic_publish(exchange='',
                              routing_key='hello',
                              body=message)
        print " [x] Sent %s" % message 
   
    def listen(self):
        """
        Listen for new slaves
        """
        self.channel.start_consuming()
    
if __name__ == "__main__":
    slave = VinoSlave()
    slave.hello()
    slave.listen()
