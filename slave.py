#!/usr/bin/env python
import pika
import uuid
import socket
import sys
import cPickle
import threading 

class VinoSlaveL(thread.Thread):
    """
    Listens to master for new connections
    """ 
    def __init__(self):
        """
        Arguments:
        ip_addr -- IP Address of VINO Master
        port -- Port VINO Master is listening on
        """
        threading.Thread.__init__(self)
        self.slaves = []
        #Used to assign increasing (unique) vxlan ip addresses
        #Value of last octet 
        self.octet_val = 0 
        parameters = pika.ConnectionParameters(host='localhost')
        #This establishes connection to the rabbitmq server
        #rabbitmq-server is running on same machine as vino-master
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='rpc_queue')
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.on_request, queue='rpc_queue')

    def get_ip_addr(self):
        """
        Return IP Address
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        ip_addr = s.getsockname()[0]
        s.close()
        return ip_addr
    
    def get_vxlan_ip(self):
        self.octet_val += 1
        return "192.168.200.%s" % self.octet_val
    
    def on_request(self, ch, method, props, body):
        client_ip_addr = body
        print " [.] client IP Address: %s"  % client_ip_addr
        #TODO: check if ip address is unique
        self.slaves.append( (client_ip_addr, self.get_vxlan_ip()) )
        response = cPickle.dumps(self.slaves, cPickle.HIGHEST_PROTOCOL)
        if True: #len(slaves) == 2: 
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id = props.correlation_id),
                             body=response) 
            ch.basic_ack(delivery_tag = method.delivery_tag)

    def start_consuming(self):
        print " [x] Awaiting RPC requests"
        self.channel.start_consuming()

    def run(self):
        self.start_consuming()

class VinoSlave(threading.Thread):
    """
    Sends self ip address to ViNO master 
    """
    def __init__(self, ip_addr, port):
        """
        Arguments:
        ip_addr -- IP Address of VINO Master
        port -- Port VINO Master is listening on
        """
        threading.Thread.__init__(self)
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters=pika.ConnectionParameters(ip_addr, port, '/', credentials)
        self.connection = pika.BlockingConnection(parameters)

        self.channel = self.connection.channel()
        #For first contact 
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

        #For listening for new slaves
        self.channel.exchange_declare(exchange='logs', type='fanout')
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        self.channel.queue_bind(exchange='logs',
                        queue=queue_name)

        self.channel.basic_consume(self.callback,
                              queue=queue_name,
                              no_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def communicate(self):
    """ 
    Communicates with the ViNO Master
    """
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key='rpc_queue',
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=str(self.get_ip_addr()))
    
        #Loop until self.response is written out
        while self.response is None:
            self.connection.process_data_events()
        return self.response

    def callback(self, ch, method, properties, body):
        print " [x] %r" % (body,)

    def get_ip_addr(self):
    """
    Returns IP address  
    """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        ip_addr = s.getsockname()[0]
        s.close()
        return ip_addr

    def start_listening(self):
        self.channel.start_consuming()

if __name__ == "__main__":
    #IP ADDR of VINO master
    ip_addr = sys.argv[1] if len(sys.argv) > 1 else "10.12.1.53"
    port = 5672 
    client = VinoSlave(ip_addr, port)
    print " [x] Requesting server IP Address"
    response = cPickle.loads(client.communicate())
    print " [.] Got %r" % (response,)

    print "Now listening for new slaves"
    client.start_listening()
