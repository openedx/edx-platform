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

apt-key update -y

# Required for add-apt-repository
apt-get install -y software-properties-common
if [[ "${SHORT_DIST}" != bionic ]] && [[ "${SHORT_DIST}" != xenial ]] && [[ "${SHORT_DIST}" != focal ]] ;then
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
sudo apt-get update -y
sudo apt-get install -y python-apt python-jinja2 build-essential sudo git-core libmysqlclient-dev libffi-dev \
libssl-dev libxml2-dev libxmlsec1-dev libxmlsec1-openssl
