#!/usr/bin/env bash
set -e

###############################################################################
#
#   all-tests.sh
#
#   Execute tests for edx-platform. This script is designed to be the
#   entry point for various CI systems.
#
###############################################################################

echo 'Printing environment variables'
env

echo 'Machine specs'
top -n 1 | head -n 20

echo '-------------------'

echo 'CPU information'
lscpu

echo '-------------------'

echo 'Linux release'
lsb_release -a

echo '-------------------'

echo 'Google Chrome version'
google-chrome --version

echo '-------------------'

echo 'Google Chrome driver version'
# Port 80 should fail, and that's what I want!
chromedriver --port=80 || true

echo '-------------------'

echo 'XVFB status'
dpkg -l xvfb || true

echo '-------------------'

echo 'Machine meta data'
curl http://169.254.169.254/latest/meta-data/

echo '-------------------'

echo 'Python virtualenv info'
ls -lah $HOME/edx-venv_clean.tar.gz

echo '-------------------'

echo 'dpkg -l'
dpkg -l

echo '-------------------'

echo 'pip freeze'
# Reset the jenkins worker's virtualenv back to the
# state it was in when the instance was spun up.
if [ -e $HOME/edx-venv_clean.tar.gz ]; then
    rm -rf $HOME/edx-venv
    tar -C $HOME -xf $HOME/edx-venv_clean.tar.gz
fi

bash -c 'source $HOME/edx-venv/bin/activate && pip freeze'

echo '-------------------'

echo 'ls -lah for pip packages'
ls -lah source $HOME/edx-venv/lib/python2.7/

echo '-------------------'

API_USER="8Rux9wlxnWrt4crm6GaReksEpPliv8"
API_PASS="dAZVV5MoMTEv7MaX5NClW7b7ltcL7X"
END_POINT="https://edraak-omar.smartfile.com/api/2/path/data/venvs/"


hostname
HOSTNAME=`hostname`

ENV_TGZ="$HOME/edx-venv_clean.tar.gz"
NAMED_ENV_TGZ="/tmp/$HOSTNAME-edx-venv_clean.tar.gz"
cp "$ENV_TGZ" "$NAMED_ENV_TGZ"

curl -v -u "$API_USER:$API_PASS" "$END_POINT" -F upload=@$NAMED_ENV_TGZ
