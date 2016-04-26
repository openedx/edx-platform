#!/usr/bin/env bash
echo "Setting up for accessibility tests..."
source scripts/jenkins-common.sh

echo "Running explicit accessibility tests..."
SELENIUM_BROWSER=phantomjs paver test_a11y

echo "Generating coverage report..."
paver a11y_coverage
