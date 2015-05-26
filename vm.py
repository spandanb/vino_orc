import pika


#Master receiver
def receive():    
    connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
    channel = connection.channel()
    
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
    connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
    channel = connection.channel()
    
    channel.exchange_declare(exchange='logs',
                             type='fanout')
    
    message = "info: Hello World! from master"
    channel.basic_publish(exchange='logs',
                          routing_key='',
                          body=message)
    print " [x] Sent %r" % (message,)
    connection.close()

bcast()
