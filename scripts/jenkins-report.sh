#!/usr/bin/env bash
source scripts/jenkins-common.sh

# Get the diff coverage and html reports for unit tests
paver coverage

# Get coverage reports for bok choy
# paver bokchoy_coverage

# JUnit test reporter will fail the build
# if it thinks test results are old
touch `find . -name *.xml` || true
