#!/bin/bash

# Install prerequisite packages
#sudo apt-get install python g++ make checkinstall
#mkdir ~/src && cd $_
#wget -N http://nodejs.org/dist/node-latest.tar.gz
#tar -xzvf node-latest.tar.gz && cd node-v*
#./configure
#checkinstall #
#sudo dpkg -i node_*
sudo apt-get update && sudo apt-get upgrade
sudo apt-get install linux-headers-`uname -r` build-essential denyhosts screen psad nfs-kernel-server nfs-common rake locate git python-software-properties libgl1-mesa-glx libpython2.7 libqt4-network libqt4-opengl libqtcore4 libqtgui4 libsdl1.2debian libxcursor1 libxinerama1
git clone https://github.com/zenfactory/edx-platform.git 
edx-platform/scripts/create-dev-env.sh
#workon edx-platform
#cd edx-platform
#rake lms[cms.dev,0.0.0.0:8000]
