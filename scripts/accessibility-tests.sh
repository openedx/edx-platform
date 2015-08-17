#!/usr/bin/env bash
echo "Setting up for accessibility tests..."
source scripts/jenkins-common.sh

echo "Running explicit accessibility tests..."
SELENIUM_BROWSER=phantomjs paver test_bokchoy -d accessibility
