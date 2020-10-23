#!/usr/bin/env bash

set -xe

SHORT_DIST="bionic" # Update this if you update ubuntu version
PIP_VERSION="20.0.2"
SETUPTOOLS_VERSION="44.1.0"
WHEEL_VERSION="0.34.2"
EDX_PPA_KEY_SERVER="keyserver.ubuntu.com"
EDX_PPA_KEY_ID="B41E5E3969464050"


if [[ $(id -u) -ne 0 ]] ;then
    echo "Please run as root";
    exit 1;
fi

if grep -q 'Trusty Tahr' /etc/os-release
then
    SHORT_DIST="trusty"
elif grep -q 'Xenial Xerus' /etc/os-release
then
    SHORT_DIST="xenial"
elif grep -q 'Bionic Beaver' /etc/os-release
then
    SHORT_DIST="bionic"
elif grep -q 'Focal Fossa' /etc/os-release
then
    SHORT_DIST="focal"
else
    cat << EOF

    This script is only known to work on Ubuntu Trusty, Xenial, and Bionic;
    exiting.
EOF
   exit 1;
fi

EDX_PPA="deb http://ppa.edx.org ${SHORT_DIST} main"

# Upgrade the OS
rm -r /var/lib/apt/lists/* -vf
apt-get update -y

# To apt-key update in bionic, gnupg is needed.
if [[ "${SHORT_DIST}" == bionic ]] ;then
  apt-get install -y gnupg
fi

apt-key update -y

# Required for add-apt-repository
apt-get install -y software-properties-common
if [[ "${SHORT_DIST}" != bionic ]] && [[ "${SHORT_DIST}" != xenial ]] && [[ "${SHORT_DIST}" != focal ]] ;then
  apt-get install -y python-software-properties
fi

# Add git PPA
add-apt-repository -y ppa:git-core/ppa

# For older software we need to install our own PPA
# Phased out with Ubuntu 18.04 Bionic and Ubuntu 20.04 Focal
if [[ "${SHORT_DIST}" != bionic ]] && [[ "${SHORT_DIST}" != focal ]] ;then
  apt-key adv --keyserver "${EDX_PPA_KEY_SERVER}" --recv-keys "${EDX_PPA_KEY_ID}"
  add-apt-repository -y "${EDX_PPA}"
fi

# Add deadsnakes repository for python3.5 usage in
# Ubuntu versions different than xenial.
if [[ "${SHORT_DIST}" != xenial ]] ;then
  add-apt-repository -y ppa:deadsnakes/ppa
fi

apt-get update -y
apt-get install -y python3-apt python3-jinja2 build-essential sudo git-core libmysqlclient-dev libffi-dev \
libssl-dev libxml2-dev libxmlsec1-dev libxmlsec1-openssl

python3 -m pip install --upgrade pip=="${PIP_VERSION}"
python3 -m pip install setuptools=="${SETUPTOOLS_VERSION}"
python3 -m pip install wheel=="${WHEEL_VERSION}"
