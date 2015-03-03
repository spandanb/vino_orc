#!/usr/bin/env python
import pika
import socket


slaves = []
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))

channel = connection.channel()

channel.queue_declare(queue='rpc_queue')

def get_ip_addr():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8",80))
    ip_addr = s.getsockname()[0]
    s.close()
    return ip_addr

count = 0  
def get_vxlan_ip():
    global count 
    count += 1
    return "192.168.200.%s" % count

def on_request(ch, method, props, body):
    client_ip_addr = body
    global slaves
    print " [.] client IP Address: %s"  % client_ip_addr
    slaves.append( (client_ip_addr, get_vxlan_ip()) )
    if len(slaves) == 2: 
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id = props.correlation_id),
                         body=slaves)
        ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue='rpc_queue')

print " [x] Awaiting RPC requests"
channel.start_consuming()
