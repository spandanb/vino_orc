#!/usr/bin/env python
import pika
import uuid
import socket
import sys
import cPickle
import threading 
from utils import get_ip_addr

class VinoSlave():
    """
    Sends self ip address to ViNO master 
    and listens for incommu
    """
    def __init__(self, ip_addr, port):
        """
        Arguments:
        ip_addr -- IP Address of VINO Master
        port -- Port VINO Master is listening on
        """
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters=pika.ConnectionParameters(ip_addr, port, '/', credentials)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.slaves = {}

        #For first contact 
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

        #For listening for new slaves
        self.channel.exchange_declare(exchange='logs', type='fanout')
        result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        self.channel.queue_bind(exchange='logs',
                        queue=queue_name)

        self.channel.basic_consume(self.callback,
                              queue=queue_name,
                              no_ack=True)

    def on_response(self, ch, method, props, body):
        """
        On response from initial contact
        """
        if self.corr_id == props.correlation_id:
            self.response = cPickle.loads(body)

    def contact_master(self):
        """ 
        Contacts ViNO Master, and sends own
        IP address
        response is dictionary of existing slaves 
        """
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key='rpc_queue',
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=str(get_ip_addr()))
    
        #Loop until self.response is written out
        while self.response is None:
            self.connection.process_data_events()
        self.slaves = self.response
        return self.response

    def callback(self, ch, method, properties, body):
        """
        When new slave broadcast
        """
        body = cPickle.loads(body)
        print "Received: %r" % (body,)
        self.slaves[body[0]] = body[1]
        
    def start_listening(self):
        """
        Listen for new slaves
        """
        self.channel.start_consuming()

if __name__ == "__main__":
    #IP ADDR of VINO master
    ip_addr = sys.argv[1] if len(sys.argv) > 1 else "10.12.1.53"
    port = 5672 
    node = VinoSlave(ip_addr, port)
    print " [x] Requesting server IP Address"
    response = node.contact_master()
    print " [.] Got %r" % (response,)

    print "Now listening for new slaves"
    node.start_listening()
