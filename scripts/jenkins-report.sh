#!/usr/bin/env bash

# This script is used by the edx-platform-unit-coverage jenkins job.

source scripts/jenkins-common.sh

# Get the diff coverage and html reports for unit tests
paver coverage

# Send the coverage data to coveralls. Setting 'TRAVIS_BRANCH' allows the
# data to be sorted by branch in the coveralls UI. The branch is passed as
# a param to the coverage job on jenkins.
#pip install coveralls==1.0
#COVERALLS_REPO_TOKEN=$1 TRAVIS_BRANCH=$2 coveralls
pip install codecov==2.0.5
CODE_COV_TOKEN=$1
codecov --token=$CODE_COV_TOKEN

# Get coverage reports for bok choy
# paver bokchoy_coverage

# JUnit test reporter will fail the build
# if it thinks test results are old
touch `find . -name *.xml` || true
