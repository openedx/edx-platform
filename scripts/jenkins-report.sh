#!/usr/bin/env bash
set -e

# This script generates coverage and diff cover reports, and optionally
# reports this data to codecov.io. The following environment variables must be
# set in order to report to codecov:
# CODE_COV_TOKEN: CodeCov API token
# CI_BRANCH: The branch that the coverage report describes

# This script is used by the edx-platform-unit-coverage jenkins job.

source scripts/jenkins-common.sh

# Get the diff coverage and html reports for unit tests
paver coverage

# Test for the CodeCov API token
if [ -z $CODE_COV_TOKEN ]; then
    echo "codecov.io API token not set."
    echo "This must be set as an environment variable if order to report coverage"
else
    # Send the coverage data to codecov
    pip install codecov==2.0.5
    codecov --token=$CODE_COV_TOKEN --branch=$CI_BRANCH
fi

# JUnit test reporter will fail the build
# if it thinks test results are old
touch `find . -name *.xml` || true
