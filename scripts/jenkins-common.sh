#!/usr/bin/env bash

set -e

source $HOME/jenkins_env

# Clear the mongo database
# Note that this prevents us from running jobs in parallel on a single worker.
mongo --quiet --eval 'db.getMongo().getDBNames().forEach(function(i){db.getSiblingDB(i).dropDatabase()})'

# Ensure we have fetched origin/master
# Some of the reporting tools compare the checked out branch to origin/master;
# depending on how the GitHub plugin refspec is configured, this may
# not already be fetched.
git fetch origin master:refs/remotes/origin/master

# Reset the jenkins worker's virtualenv back to the
# state it was in when the instance was spun up.
if [ -e $HOME/edx-venv_clean.tar.gz ]; then
    rm -rf $HOME/edx-venv
    tar -C $HOME -xf $HOME/edx-venv_clean.tar.gz
fi

# Activate the Python virtualenv
source $HOME/edx-venv/bin/activate

# add the node_js packages dir to PATH
PATH=$PATH:node_modules/.bin

# Manage the npm cache on Jenkins.
# (In this case, remove it. That ensures from run-to-run, it is a clean npm environment)
echo "--> Cleaning npm cache"
npm cache clean

# Log any paver or ansible command timing
TIMESTAMP=$(date +%s)
export PAVER_TIMER_LOG="test_root/log/timing.paver.$TIMESTAMP.log"
export ANSIBLE_TIMER_LOG="test_root/log/timing.ansible.$TIMESTAMP.log"
