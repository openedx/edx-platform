#!/usr/bin/env bash
set -e

###############################################################################
#
# Usage:
#   To run just tests, without pa11ycrawler:
#       ./scripts/accessibility-tests.sh
#
#   To run tests, followed by pa11ycrawler:
#       RUN_PA11YCRAWLER=1 ./scripts/accessibility-tests.sh
#
###############################################################################

echo "Setting up for accessibility tests..."
source scripts/jenkins-common.sh

echo "Running explicit accessibility tests..."
SELENIUM_BROWSER=phantomjs paver test_a11y --with-xunitmp

echo "Generating coverage report..."
paver a11y_coverage

echo "Running pa11ycrawler against test course..."
paver pa11ycrawler --fasttest --skip-clean --fetch-course --with-html

echo "Generating coverage report..."
paver pa11ycrawler_coverage
