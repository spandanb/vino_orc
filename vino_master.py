#!/usr/bin/env python
import pika
import socket
import cPickle
import threading

#TODO: race conditions if 2 slaves join at the same time?

class VinoMasterW(threading.Thread):
    """
    Push information about new slaves to 
    existing slaves
    """
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
class VinoMasterL(threading.Thread):
    """ VINO Master- listens for new slaves and responds, 
    i.e.pushes information about existing slaves to this slave
    This is based on the RPC design pattern
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.slaves = []
        #Used to assign increasing (unique) vxlan ip addresses
        #Value of last octet 
        self.octet_val = 0 

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
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


if __name__ == "__main__":
    master = VinoMasterL()
    #master.start_consuming()
    master.start()
