#!/usr/bin/python

import pika
import sys

#Create a connection with the broker
host = '10.12.1.53' #'localhost'

credentials = pika.PlainCredentials('guest', 'guest')
parameters=pika.ConnectionParameters(host, 5672, '/', credentials)

connection = pika.BlockingConnection(parameters)


channel = connection.channel()

#Declare a queue
channel.queue_declare(queue='myQueue')

msg = sys.argv[1] if len(sys.argv) > 1 else "Hello World"

channel.basic_publish(exchange='',
                      routing_key='myQueue',
                      body=msg)

print " [x] Sent {}".format(msg)

connection.close()
