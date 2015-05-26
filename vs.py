import pika

ip_addr = "10.12.1.53"
port = 5672 
credentials = pika.PlainCredentials('guest', 'guest')
parameters=pika.ConnectionParameters(ip_addr, port, '/', credentials)
connection = pika.BlockingConnection(parameters)

channel = connection.channel()

#Slave send        
def send():
    channel.queue_declare(queue='hello')
    
    channel.basic_publish(exchange='',
                          routing_key='hello',
                          body='Hello World!')
    print " [x] Sent 'Hello World!'"

    #connection.close() #Closes connection with master

#slave listen
def receive():
    channel.exchange_declare(exchange='logs',
                             type='fanout')
    
    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    
    channel.queue_bind(exchange='logs',
                       queue=queue_name)
    
    print ' [*] Waiting for logs. To exit press CTRL+C'
    
    def callback(ch, method, properties, body):
        print " [x] %r" % (body,)
    
    channel.basic_consume(callback,
                          queue=queue_name,
                          no_ack=True)
    
    channel.start_consuming()

def fuse():
    #configire for receive
    channel.queue_declare(queue='hello')

    #configure for send
    channel.exchange_declare(exchange='bcast', type='fanout')

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue
    
    channel.queue_bind(exchange='bcast',
                       queue=queue_name)
    
    print ' [*] Waiting for slaves. To exit press CTRL+C'
    
    #callback for something received 
    def callback(ch, method, properties, body):
        print " [x] %r" % (body,)
   
    #This configures consume function, but doesn't 
    # start consuming
    channel.basic_consume(callback,
                          queue=queue_name,
                          no_ack=True)

    channel.basic_publish(exchange='',
                          routing_key='hello',
                          body='Hello World!')
    print " [x] Sent 'Hello World!'"
    channel.start_consuming()

fuse()
