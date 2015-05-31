Overview
========
Creates overlay of complete mesh over nodes
ViNOMaster facilitates by acting as naming service.

The vino_master and vino_slave modules support 
basic bidirectional communication. Specifically, 

VinoMaster listens for incoming slaves and broadcasts 
this to existing slaves


The goal is to be able to:
==========================
1) Boot a Master
2) Boot multiple slaves
3) Create VXLAN tunnel- mesh between masters and slaves
4) Dynamically add slaves that can be meshed in

Next Steps
==========
Connect the ovs in slaves to controller (RYU)
    possibly many controllers, managing different slices?
Connect controllers using Janus
    use janus port register/de-register

Use fab for configuring slaves- centralized approach
    master executes commands on slaves
Use coreos + containers to configure slaves- distributed approach
    -possibly use fabfile to start this configuration
