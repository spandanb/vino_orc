import pika
import sys


parameters = pika.ConnectionParameters(host='localhost')
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

channel.exchange_declare(exchange='logs', type='fanout')

message =  "info: Hello World!"
#Sends the actual message
channel.basic_publish(exchange='logs',
                      routing_key='',
                      body=message)

print " [x] Sent %r" % (message,)
connection.close()
