#!/bin/bash 

#### Ubuntu Precise (12.04x) ####
# For installation on a clean system
####

#######################
# Variable declarations
# FILL THESE IN ACCORDINGLY FOR YOUR CONFIGURATION / SETUP
#######################
SYSTEM_HOST_NAME='edx'
SYSTEM_DOMAIN_NAME='vedaproject.org'
SYSTEM_FQDN="$SYSTEM_HOST_NAME.$SYSTEM_DOMAIN_NAME"
emailUser=''
emailPass=''
emailFQDN=''

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

# Optional, remove the iptables commands if you do not want your CMS running on port 80 (or if you do not have sudo access to the system)
# Create a startup script for Studio
echo "#!/bin/bash" > ~/start-cms.sh
echo ". /etc/bash_completion.d/virtualenvwrapper; sudo iptables -F; sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8000; workon edx-platform; cd ~/edx-platform; rake cms[dev,0.0.0.0:8001];" >> ~/start-cms.sh

# Set permissions on edX startup script
chmod +x ~/quickStarts/start-lms.sh

# Set permissions on Studio startup script
chmod +x ~/quickStarts/start-cms.sh

# Reconfigure postfix ( use the following values [default all + remove FQDN of server when asked for which hosts this machine is the final destination] 
sudo dpkg-reconfigure postfix

# Configure machine's host name
sudo hostname $SYSTEM_FQDN

############
# Optional
# Setup mail transport
############

# Setup Google Managed domain settings in postfix
sudo cat ~/edx-platform/quickStarts/postfix-config.append >> /etc/postfix/main.cf
sudo cat ~/edx-platform/quickStarts/postfix-auth.append >> /etc/postfix/sasl_passwd
sudo chmod 400 /etc/postfix/sasl_passwd
sudo postmap /etc/postfix/sasl_passwd
cat /etc/ssl/certs/Thawte_Premium_Server_CA.pem | sudo tee -a /etc/postfix/cacert.pem
sudo /etc/init.d/postfix reload

# Start Studio and edX in a detached screen session.
screen -d -m ~/quickStarts/start-edx.sh
