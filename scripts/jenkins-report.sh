#!/usr/bin/env bash
source scripts/jenkins-common.sh

# Combine the data files that were generated using -p
paver combine_jenkins_coverage

# Get the diff coverage and html reports for unit tests
paver coverage

# JUnit test reporter will fail the build
# if it thinks test results are old
touch `find . -name *.xml` || true
