#!/bin/bash

wget "https://raw.githubusercontent.com/spandanb/utils/master/.screenrc"
wget "https://raw.githubusercontent.com/spandanb/utils/master/.vimrc"

#echo "Cloning vino_orc repo"
#git clone https://github.com/spandanb/vino_orc.git /home/ubuntu/vino_orc

cd /home/ubuntu/vino_orc

echo "Creating screen session"
screen -d -m -S my_screen -t shell -s bash

echo "Creating tab"
screen -S my_screen -X screen -t my_screen_tab

sleep 2

echo "running slave"
#screen -S my_screen -p my_screen_tab -X stuff 'python vs.py'`echo -ne '\015'`
screen -S my_screen -p 1 -X stuff 'python vs.py
'





