import subprocess as sp
import re

def get_tun_ip():
    """
    Get Tun0 IP of host
    """
    try:
        tun0 = sp.check_output(["ifconfig", "tun0"])
        tun0 = re.search("(?<=inet addr:)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", tun0)
        tun_ip = tun0.group()
        return tun_ip
    except sp.CalledProcessError as err:
        return ""

