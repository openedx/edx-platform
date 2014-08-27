#!/usr/bin/env bash
set -e

###############################################################################
#
#   edx-acceptance.sh
#
#   Execute acceptance tests for edx-platform.
#
#   This script can be called from a Jenkins
#   job that defines these environment variables:
#
#   `TEST_SUITE` defines which acceptance test suite to run
#   Possible values are:
#
#       - "lms": Run the acceptance (Selenium) tests for the LMS
#       - "cms": Run the acceptance (Selenium) tests for Studio
#
#   `FEATURE_PATH` is the path to the lettuce .feature file
#       containing the tests to run.  If empty, run all the tests.
#
#   Other assumptions:
#
#   - The edx-platform git repository is checked out by the Jenkins git plugin.
#
#   - Jenkins logs in as user "jenkins"
#
#   - The Jenkins file system root is "/home/jenkins"
#
#   - An init script creates a virtualenv at "/home/jenkins/edx-venv"
#     with some requirements pre-installed (such as scipy)
#
#  Jenkins worker setup:
#  See the edx/configuration repo for Jenkins worker provisioning scripts.
#  The provisioning scripts install requirements that this script depends on!
#
###############################################################################

source $HOME/jenkins_env

# Clean up previous builds
git clean -qxfd

# Clear the mongo database
# Note that this prevents us from running jobs in parallel on a single worker.
mongo --quiet --eval 'db.getMongo().getDBNames().forEach(function(i){db.getSiblingDB(i).dropDatabase()})'

# Ensure we have fetched origin/master
# Some of the reporting tools compare the checked out branch to origin/master;
# depending on how the GitHub plugin refspec is configured, this may
# not already be fetched.
git fetch origin master:refs/remotes/origin/master

# Reset the jenkins worker's ruby environment back to
# the state it was in when the instance was spun up.
if [ -e $HOME/edx-rbenv_clean.tar.gz ]; then
    rm -rf $HOME/.rbenv
    tar -C $HOME -xf $HOME/edx-rbenv_clean.tar.gz
fi

# Bootstrap Ruby requirements so we can run the tests
bundle install

# Ensure the Ruby environment contains no stray gems
bundle clean --force

# Reset the jenkins worker's virtualenv back to the
# state it was in when the instance was spun up.
if [ -e $HOME/edx-venv_clean.tar.gz ]; then
    rm -rf $HOME/edx-venv
    tar -C $HOME -xf $HOME/edx-venv_clean.tar.gz
fi

# Activate the Python virtualenv
source $HOME/edx-venv/bin/activate

paver test_acceptance -s ${TEST_SUITE} --extra_args="-v 3 ${FEATURE_PATH}"
