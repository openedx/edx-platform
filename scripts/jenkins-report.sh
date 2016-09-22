#!/usr/bin/env bash

# This script is used by the edx-platform-unit-coverage jenkins job.

if [ $# -eq 1 ]; then
    COMMIT=$1
else
    echo "Incorrect number of arguments passed to this script!"
    echo "Please supply a git hash to specify the commit being tested"
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
codecov --token=$CODE_COV_TOKEN --commit=$COMMIT

# Get coverage reports for bok choy
# paver bokchoy_coverage

# JUnit test reporter will fail the build
# if it thinks test results are old
touch `find . -name *.xml` || true
