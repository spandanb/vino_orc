#!/usr/bin/env python

import pika
import cPickle
import threading

#TODO: race conditions if 2 slaves join at the same time?
#TODO: handle conditions like clients die 

class VinoMaster(object):
    """ VINO Master- listens for new slaves and responds, 
    i.e.pushes information about existing slaves to this slave
    This is based on the RPC design pattern
    Also broadcasts info about new slaves to old slaves
    """
    def __init__(self):
        self.slaves = {}
        #Used to assign increasing (unique) vxlan ip addresses
        #Value of last octet 
        self.octet_val = 0 
        parameters = pika.ConnectionParameters(host='localhost')
        #This establishes connection to the rabbitmq server
        #rabbitmq-server is running on same machine as vino-master
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        #for new slave 
        self.channel.queue_declare(queue='rpc_queue')
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.on_new_slave, queue='rpc_queue')

        #for existing slaves
        self.channel.exchange_declare(exchange='logs', type='fanout')

    def get_vxlan_ip(self):
        """
        Returns a unique VXLAN IP address
        e.g. 192.168.200.1
        Note: This will only work for upto 255 hosts
        """
        self.octet_val += 1
        return "192.168.200.%s" % self.octet_val
    
    def on_new_slave(self, ch, method, props, body):
        """
        Response when new slave contacts masters
        Record that slave
        and broadcast info to existing slaves
        """
        slave_ip = body
        print " [.] slave IP Address: %s"  % client_ip_addr
        if slave_ip not in slaves:
            slaves[slave_ip] = self.get_vxlan_ip()
        new_slave = (slave_ip, slaves[slave_ip])
        #Response to new slave
        response = cPickle.dumps(self.slaves, cPickle.HIGHEST_PROTOCOL)
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id = props.correlation_id),
                         body=response) 
        ch.basic_ack(delivery_tag = method.delivery_tag)
        
        #Broadcast new slave    
        print " [x] Sent %r" % new_slave 
        self.broadcast(message=
            cPickle.dumps(new_slave, cPickle.HIGHEST_PROTOCOL))

    def broadcast(self, message):
        """
        broadcast to existing slaves
        """
        self.channel.basic_publish(exchange='logs',
                              routing_key='',
                              body=message)

    def start_listening(self):
        """
        Start listening for new slaves
        """
        print " [x] Awaiting connections from slaves"
        self.channel.start_consuming()

    def cleanup(self):
        self.connection.close()

if __name__ == "__main__":
    master = VinoMaster()
    master.start_listening()
