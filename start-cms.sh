#!/bin/bash
. /etc/bash_completion.d/virtualenvwrapper; 
workon edx-platform
cd ~/edx-platform
rake cms[dev,0.0.0.0:8001];
