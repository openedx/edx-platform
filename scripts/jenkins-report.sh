#!/usr/bin/env bash

# Note: this script is in a temporary state. In an effort to get the
# platform off of coveralls and onto codecov, we will be temporarily
# using both. In order to no longer use coveralls, a change must be
# made in https://github.com/edx/jenkins-job-dsl, as well as removing
# the coveralls block below

# This script is used by the edx-platform-unit-coverage jenkins job.

if [ $# -eq 2 ]; then
    if [ $2 == "master" ]; then
        # get the git hash for this commit on master
        COMMIT=`git rev-parse HEAD`
    else
        COMMIT=$2
    fi
else
    echo "Incorrect number of arguments passed to this script!"
    echo "Please supply the following values to this script:"
    echo "1) git hash of the commit being tested"
    echo "2) coveralls token"
    exit 1
fi

source scripts/jenkins-common.sh

# Get the diff coverage and html reports for unit tests
paver coverage

# Send the coverage data to codecov. Setting the 'COMMMIT' allows the data
# to be sorted by a branch in the codecov UI. The branch is passed as a
# param to the coverage job on Jenkins. The 'CODE_COV_TOKEN' should be
# available as an environment variable.
pip install codecov==2.0.5
codecov --token=$CODE_COV_TOKEN --commit=$COMMIT --required

# THIS BLOCK WILL BE REMOVED
# Send the coverage data to coveralls. Setting 'TRAVIS_BRANCH' allows the
# data to be sorted by branch in the coveralls UI. The branch is passed as
# a param to the coverage job on jenkins.
pip install coveralls==1.0
COVERALLS_REPO_TOKEN=$1 TRAVIS_BRANCH=$COMMIT coveralls

# Get coverage reports for bok choy
# paver bokchoy_coverage

# JUnit test reporter will fail the build
# if it thinks test results are old
touch `find . -name *.xml` || true
