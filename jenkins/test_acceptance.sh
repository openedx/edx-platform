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
    virtualenv /mnt/virtualenvs/"$JOB_NAME"
fi

export PIP_DOWNLOAD_CACHE=/mnt/pip-cache

source /mnt/virtualenvs/"$JOB_NAME"/bin/activate
pip install -q -r pre-requirements.txt
yes w | pip install -q -r requirements.txt

bundle install

npm install

rake clobber

TESTS_FAILED=0

# Assumes that Xvfb has been started by upstart
# and is capturing display :1
# The command for this is:
# /usr/bin/Xvfb :1 -screen 0 1024x268x24
# This allows us to run Chrome without a display
export DISPLAY=:1

# Run the lms and cms acceptance tests
rake test_acceptance_lms || TESTS_FAILED=1
rake test_acceptance_cms || TESTS_FAILED=1

[ $TESTS_FAILED == '0' ]
