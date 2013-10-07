#!/bin/bash

# Variable Declarations
edXPath='/home/hshirani/edx-platform/quickStarts'

# Flush any iptable rules
sudo iptables -F; 

# Setup port forwarding
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8000;

# Start LMS in screen session
screen -d -m $edXPath/start-lms.sh

# Start CMS in screen session
screen -d -m $edXPath/start-cms.sh
