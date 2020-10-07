#!/usr/bin/env bash

set -xe

SHORT_DIST="xenial" # Update this if you update ubuntu version

# Bootstrapping constants
PIP_VERSION="9.0.3"
EDX_PPA_KEY_SERVER="keyserver.ubuntu.com"
EDX_PPA_KEY_ID="B41E5E3969464050"

if [[ $(id -u) -ne 0 ]]; then
    echo "Please run as root"
    exit 1
fi

EDX_PPA="deb http://ppa.edx.org ${SHORT_DIST} main"

apt-get update -y
apt-key update -y

# Required for add-apt-repository
apt-get install -y software-properties-common
if [[ "${SHORT_DIST}" != bionic ]]; then
    apt-get install -y python-software-properties
fi

# Add git PPA
add-apt-repository -y ppa:git-core/ppa

# For older software we need to install our own PPA
# Phased out with Ubuntu 18.04 Bionic
if [[ "${SHORT_DIST}" != bionic ]]; then
    apt-key adv --keyserver "${EDX_PPA_KEY_SERVER}" --recv-keys "${EDX_PPA_KEY_ID}"
    add-apt-repository -y "${EDX_PPA}"
fi

# Install python 2.7 latest, git and other common requirements
# NOTE: This will install the latest version of python 2.7 and
apt-get update -y

pip install --upgrade pip=="${PIP_VERSION}"

echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/4.4 multiverse" |
    sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list
sudo apt-get update -y # Upgrade the OS
sudo apt-get install -y python2.7 python2.7-dev python-pip python-apt python-yaml python-jinja2 build-essential \
    sudo git-core libmysqlclient-dev libffi-dev libssl-dev python-software-properties pkg-config gfortran \
    libatlas-dev libblas-dev liblapack-dev curl git python-virtualenv python-scipy python-numpy python-dev gfortran \
    libfreetype6-dev libpng12-dev gcc libjpeg-dev libtiff5-dev zlib1g-dev libxml2-dev libxslt-dev yui-compressor \
    graphviz libgraphviz-dev g++ graphviz-dev libgeos-dev libreadline6 libreadline6-dev nodejs mysql-client \
    virtualenvwrapper libgeos-ruby1.8 lynx-cur libxmlsec1-dev swig software-properties-common \
    python-software-properties libsqlite3-dev mysql-server mongodb-org
sudo apt-get update -y # Upgrade the OS
