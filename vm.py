import pika


connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
channel = connection.channel()

#Master receiver
def receive():    
    channel.queue_declare(queue='hello')
    
    print ' [*] Waiting for messages. To exit press CTRL+C'
    
    def callback(ch, method, properties, body):
        print " [x] Received %r" % (body,)
    
    channel.basic_consume(callback,
                          queue='hello',
                          no_ack=True)
    
    channel.start_consuming()

#Master broadcast
def bcast():
    channel.exchange_declare(exchange='logs',
                             type='fanout')
    
    message = "info: Hello World! from master"
    channel.basic_publish(exchange='logs',
                          routing_key='',
                          body=message)
    print " [x] Sent %r" % (message,)
    connection.close()


def fuse():
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

fuse()
