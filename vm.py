import pika
from cPickle import dumps, HIGHEST_PROTOCOL as HP
from utils import get_vxlan_ip 

def vinoMaster():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    channel.queue_declare(queue='hello') #For receive
    channel.exchange_declare(exchange='bcast', #For bcast
                             type='fanout')
    
    print ' [*] Waiting for slaves. To exit press CTRL+C'

    def callback(ch, method, properties, body):
        print " [x] Received %r" % (body,)
        
        #To send 
        message = "info: Hello World! from master"
        channel.basic_publish(exchange='bcast',
                              routing_key='',
                              body=message)
        print " [x] Sent %r" % (message,)
    
    channel.basic_consume(callback,
                          queue='hello',
                          no_ack=True)
    
    channel.start_consuming()

class VinoMaster(object):
    def __init__(self):
        #Map of slave IP addresses to VXLAN IP addresses
        self.slaves = {}
        #Create connection
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        #Create channel
        self.channel = connection.channel()

        self.channel.queue_declare(queue='hello') #For receive
        self.channel.exchange_declare(exchange='bcast', #For bcast
                                 type='fanout')

    def callback(self, ch, method, properties, body):
        """
        Respond to incoming slaves
        """
        #Would need to modify if supporting delete
        print " [x] Received %r" % (body,)
        self.slaves[body] = get_vxlan_ip(len(self.slaves))
        
        #To send 
        message = dumps(self.slaves, HP)
        #message = "info: Hello World! from master"
        self.channel.basic_publish(exchange='bcast',
                              routing_key='',
                              body=message)
        print " [x] Sent %r" % (self.slaves,)


    def listen(self):
        self.channel.basic_consume(self.callback,
                              queue='hello',
                              no_ack=True)
        self.channel.start_consuming()

if __name__ == "__main__":
    #fuse()
    master = VinoMaster()
    master.listen()
