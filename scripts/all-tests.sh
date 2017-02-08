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

# echo 'Printing environment variables'
# env

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
