from string import Template
import sys

#Parameters
TEMPLATE_FILE = "setup_vxlan_template.sh"
INSTANCE_FILE = "setup_vxlan.sh"
VXLAN_IP = "192.168.200.1/24"
REMOTE_IP = "10.12.1.53"

if __name__ == "__main__":
    
    VXLAN_IP = sys.argv[1]
    REMOTE_IP = sys.argv[2]

    #open the file
    with open( TEMPLATE_FILE ) as template:
        #read template file
        src = Template( template.read() )
        result = src.substitute({'VXLAN_IP': VXLAN_IP, 
            'REMOTE_IP': REMOTE_IP})
        #write output
        with open(INSTANCE_FILE, 'w') as outfile:
            outfile.write(result)
            


