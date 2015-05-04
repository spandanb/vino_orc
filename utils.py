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
