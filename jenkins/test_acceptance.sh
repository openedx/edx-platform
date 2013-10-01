#! /bin/bash

set -e
set -x

git remote prune origin

# Reset the submodule, in case it changed
git submodule foreach 'git reset --hard HEAD'

# Set the IO encoding to UTF-8 so that askbot will start
export PYTHONIOENCODING=UTF-8

if [ ! -d /mnt/virtualenvs/"$JOB_NAME" ]; then
    mkdir -p /mnt/virtualenvs/"$JOB_NAME"
    virtualenv --system-site-packages /mnt/virtualenvs/"$JOB_NAME"
fi

export PIP_DOWNLOAD_CACHE=/mnt/pip-cache

source /mnt/virtualenvs/"$JOB_NAME"/bin/activate
rake install_prereqs
rake clobber

TESTS_FAILED=0

# Assumes that Xvfb has been started by upstart
# and is capturing display :1
# The command for this is:
# /usr/bin/Xvfb :1 -screen 0 1024x268x24
# This allows us to run Chrome or Firefox without a display
export DISPLAY=:1
SKIP_TESTS=""

# Testing for the existance of these environment variables
if [ ! -z ${LETTUCE_BROWSER+x} ]; then
	SKIP_TESTS="--tag -skip_$LETTUCE_BROWSER"
fi
if [ "$LETTUCE_SELENIUM_CLIENT" == saucelabs ]; then
	# SAUCE_INFO is a - seperated string PLATFORM-BROWSER-VERSION-DEVICE
	# Error checking is done in the setting up of the browser
	IFS='-' read -a SAUCE <<< "${SAUCE_INFO}"
	SKIP_TESTS="--tag -skip_sauce --tag -skip_${SAUCE[1]}"
fi

# Run the lms and cms acceptance tests
rake test:acceptance["$SKIP_TESTS"] || TESTS_FAILED=1

[ $TESTS_FAILED == '0' ]
