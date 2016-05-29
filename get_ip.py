import subprocess as sp
import re

def get_ip(interface="eth0"):
    """
    Get IP of interface of local host
    """
    try:
        intf = sp.check_output(["ifconfig", interface])
        intf = re.search("(?<=inet addr:)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", intf)
        ip = intf.group()
        return ip
    except sp.CalledProcessError as err:
        return ""

if __name__ == "__main__":
    print get_ip()
