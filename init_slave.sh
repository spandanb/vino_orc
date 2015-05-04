#!/usr/bash

#Creates screens, named my_screen and runs vino_slave in them

screen -d -m -S my_screen -t shell -s bash
screen -r my_screen -X hardstatus alwayslastline '%{= .} %-Lw%{= .}%> %n%f %t*%{= .}%+Lw%< %-=%{g}(%{d}%H/%l%{g})'
screen -S my_screen -X screen -t my_screen_tab
screen -S my_screen -p my_screen_tab -X stuff 'cd /home/ubuntu/vino_orc'`echo -ne '\015'`
screen -S my_screen -p my_screen_tab -X stuff 'python slave.py'`echo -ne '\015'`
