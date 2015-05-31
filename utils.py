import socket

def get_ip_addr(return_string=True):
    """
    Return IP Address of current host
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8",80))
    ip_addr = s.getsockname()[0]
    s.close()
    return str(ip_addr) if return_string else ip_addr

def get_vxlan_ip(n):
    """
    Returns an IP address in the range
    192.168.0.0 - 192.168.255.255
    without using X.0 or X.255
    """

    quot, rem = divmod(n, 254)  
    ip_addr = "192.168.%s.%s" % (quot + 1, rem + 1) 
    return ip_addr
