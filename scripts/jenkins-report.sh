#!/usr/bin/env bash
source scripts/jenkins-common.sh

# Run coverage again to get the diff coverage report
paver coverage

# JUnit test reporter will fail the build
# if it thinks test results are old
touch `find . -name *.xml` || true
