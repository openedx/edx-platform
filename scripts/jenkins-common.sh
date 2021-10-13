#!/usr/bin/env bash

set -e

source $HOME/jenkins_env

# Clear the mongo database
# Note that this prevents us from running jobs in parallel on a single worker.
mongo --quiet --eval 'db.getMongo().getDBNames().forEach(function(i){db.getSiblingDB(i).dropDatabase()})'

# Ensure we have fetched a target branch (origin/master, unless testing
# a release branc) Some of the reporting tools compare the checked out
# branch to a target branch; depending on how the GitHub plugin refspec
# is configured, this may not already be fetched.
if [ ! -z ${TARGET_BRANCH+x} ]; then
    TARGET_BRANCH_WITHOUT_ORIGIN=$(echo "${TARGET_BRANCH}" | sed 's:^origin/::')
    git fetch origin $TARGET_BRANCH_WITHOUT_ORIGIN:refs/remotes/origin/$TARGET_BRANCH_WITHOUT_ORIGIN
fi

# Reset the jenkins worker's virtualenv back to the
# state it was in when the instance was spun up.
if [ -z ${PYTHON_VERSION+x} ] || [[ ${PYTHON_VERSION} == 'null' ]]; then
    VENV_PATH="$HOME"
    ARCHIVED_VENV="edx-venv_clean.tar.gz"
else
    VENV_PATH="$HOME/edx-venv-$PYTHON_VERSION"
    ARCHIVED_VENV="edx-venv_clean-$PYTHON_VERSION.tar.gz"
fi

if [ -e $HOME/$ARCHIVED_VENV ]; then
    rm -rf $VENV_PATH/edx-venv
    tar -C $VENV_PATH -xf $HOME/$ARCHIVED_VENV
fi

# Load the npm packages from the time the worker was built
# into the npm cache. This is an attempt to reduce the number
# of times that npm gets stuck during an installation, by
# reducing the number of packages that npm needs to fetch.
if [ -e $HOME/edx-npm-cache_clean.tar.gz ]; then
    echo "Loading archived npm packages into the local npm cache"
    rm -rf $HOME/.npm
    tar -C $HOME -xf $HOME/edx-npm-cache_clean.tar.gz
fi

# Activate the Python virtualenv
source $VENV_PATH/edx-venv/bin/activate

# Hack to fix up egg-link files given that the virtualenv is not relocatable
sed -i "s|^/home/jenkins/shallow-clone|`pwd`|" -- \
    $VENV_PATH/edx-venv/lib/python*/site-packages/*.egg-link
pip install pip==21.3
pip install -qr requirements/edx/pip-tools.txt
pip-sync -q requirements/edx/testing.txt requirements/edx/django.txt

# add the node packages dir to PATH
PATH=$PATH:node_modules/.bin

echo "node version is `node --version`"
echo "npm version is `npm --version`"

# Log any paver or ansible command timing
TIMESTAMP=$(date +%s)
SHARD_NUM=${SHARD:="all"}
export PAVER_TIMER_LOG="test_root/log/timing.paver.$TEST_SUITE.$SHARD_NUM.log"
export ANSIBLE_TIMER_LOG="test_root/log/timing.ansible.$TIMESTAMP.log"

echo "This node is `curl http://169.254.169.254/latest/meta-data/hostname`"
