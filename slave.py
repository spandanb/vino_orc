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
    def __init__(self, ip_addr, port):
        """
        Arguments:
        ip_addr -- IP Address of VINO Master
        port -- Port VINO Master is listening on
        """
	threading.Thread.__init__(self)

    def start(self):
	pass

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

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

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

    def get_ip_addr(self):
	"""
	Returns IP address 	
	"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        ip_addr = s.getsockname()[0]
        s.close()
        return ip_addr

if __name__ == "__main__":
    #IP ADDR of VINO master
    ip_addr = sys.argv[1] if len(sys.argv) > 1 else "10.12.1.53"
    port = 5672 
    client = VinoSlave(ip_addr, port)
    print " [x] Requesting server IP Address"
    response = cPickle.loads(client.communicate())
    print " [.] Got %r" % (response,)
