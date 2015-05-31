import pika
from cPickle import loads
from utils import get_ip_addr

def fuse():
    ip_addr = "10.12.1.53" #Master
    port = 5672 
    credentials = pika.PlainCredentials('guest', 'guest')
    parameters=pika.ConnectionParameters(ip_addr, port, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    
    channel = connection.channel()

    #configire for receive
    channel.queue_declare(queue='hello')

    #configure for send
    channel.exchange_declare(exchange='bcast', type='fanout')

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    
    channel.queue_bind(exchange='bcast',
                       queue=queue_name)
    
    #callback for something received 
    def callback(ch, method, properties, body):
        print " [x] %r" % (body,)
   
    channel.basic_publish(exchange='',
                          routing_key='hello',
                          body='Hello World!')
    print " [x] Sent 'Hello World!'"
    
    #This configures consume function, but doesn't 
    # start consuming
    channel.basic_consume(callback,
                          queue=queue_name,
                          no_ack=True)

    channel.start_consuming()

class VinoSlave(object):
    def __init__(self):
        ip_addr = "10.12.1.53" #Master
        port = 5672 
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters=pika.ConnectionParameters(ip_addr, port, '/', credentials)
        connection = pika.BlockingConnection(parameters)
        
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
        self.slaves = {}

    def callback(self, ch, method, properties, body):
        """
        callback for something received 
        """
        new_slaves = loads(body)
        #compute_diff(new_slaves, self.slaves)
        self.slaves = new_slaves
        print " [x] %r" % (self.slaves,)
    
    def hello(self):
        """
        Send initial message
        """
        message = get_ip_addr() 
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
	#fuse()
    slave = VinoSlave()
    slave.hello()
    slave.listen()
