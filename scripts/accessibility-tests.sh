#!/usr/bin/env bash
set -e


echo "Setting up for accessibility tests..."
source scripts/jenkins-common.sh

echo "Running explicit accessibility tests..."
SELENIUM_BROWSER=phantomjs paver test_a11y

echo "Generating coverage report..."
paver a11y_coverage

# The settings that we use are installed with the pa11ycrawler module
export SCRAPY_SETTINGS_MODULE='pa11ycrawler.settings'

echo "Running pa11ycrawler against test course..."
paver pa11ycrawler --fasttest --skip-clean --fetch-course --with-html

echo "Generating pa11ycrawler coverage report..."
paver pa11ycrawler_coverage
