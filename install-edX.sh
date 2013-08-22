#!/bin/bash

#### Debian Wheezy (7.x) ####
# Uncomment this if you are running in debian Wheezy, or add a repository that contains the NodeJS package to your /etc/apt/sources.list
# Don't comment out anything below however. 
# This compiles NodeJS from source and creates a debian package
# Thanks to https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager for the instruction set
# There is an issue when installed as a regular user (I have not tried as sudo). The edX setup script is unable to find the node binaries. May be as simple as adding them to your path.
#### 
#sudo apt-get install python g++ make checkinstall
#mkdir ~/src && cd $_
#wget -N http://nodejs.org/dist/node-latest.tar.gz
#tar -xzvf node-latest.tar.gz && cd node-v*
#./configure
#checkinstall #
#sudo dpkg -i node_*

#### Ubuntu Precise (12.04x) ####
# For installation on a clean system
####

# Make sure package management system is up to date (comment this out if you like, the edX script does the update also, not 100% sure if it does the upgrade. Definitely intended for installation on a clean system)
sudo apt-get update && sudo apt-get upgrade

# Install prerequisite packages (some of these -- denyhosts, psad -- are not required persay but are good for system security)
sudo apt-get install linux-headers-`uname -r` build-essential npm denyhosts screen psad nfs-kernel-server nfs-common rake locate git python-software-properties libgl1-mesa-glx libpython2.7 libqt4-network libqt4-opengl libqtcore4 libqtgui4 libsdl1.2debian libxcursor1 libxinerama1

# Run the edX (awesome) setup script
~/edx-platform/scripts/create-dev-env.sh

# Add the virtualenvwrapper includes to your login script
echo "source /etc/bash_completion.d/virtualenvwrapper" >> ~/.bashrc

# Source your login script
source ~/.bashrc

# Create a startup script for edX
echo "#!/bin/bash" > ~/start-lms.sh
echo ". /etc/bash_completion.d/virtualenvwrapper; workon edx-platform; cd ~/edx-platform; rake lms[cms.dev,0.0.0.0:8000];" >> ~/start-lms.sh

# Create a startup script for Studio
echo "#!/bin/bash" > ~/start-cms.sh
echo ". /etc/bash_completion.d/virtualenvwrapper; workon edx-platform; cd ~/edx-platform; rake cms[dev,0.0.0.0:8001];" >> ~/start-cms.sh

# Set permissions on edX startup script
chmod +x ~/start-lms.sh

# Set permissions on Studio startup script
chmod +x ~/start-cms.sh

# Start edX in a detached screen session
screen -d -m ~/start-lms.sh

# Start Studio in a detached screen session.
screen -d -m ~/start-cms.sh

# Optional #
# Setup iptables rule to make edX run on standard www port 80. Must have sudo priv change interfac name (eth0) as appropriate (use /sbin/ifconfig -a to examine your network interfaces)
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8000
