#!/usr/bin/env python
import pika
import socket
import cPickle

class VinoMaster(object):
    """ VINO Master- listens for new slaves and pushes
    information about existing slaves to other slaves
    This is based on the RPC design pattern
    """
    def __init__(self):

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
        response = cPickle.dumps(self.slaves)
        if True: #len(slaves) == 2: 
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id = props.correlation_id),
                             body=response) 
            ch.basic_ack(delivery_tag = method.delivery_tag)

    def start(self):
        print " [x] Awaiting RPC requests"
        self.channel.start_consuming()


if __name__ == "__main__":
    master = VinoMaster()
    master.start()
