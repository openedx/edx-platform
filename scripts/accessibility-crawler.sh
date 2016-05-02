#!/usr/bin/env bash
set -e

echo "Setting up for accessibility tests..."
source scripts/jenkins-common.sh

echo "Running pa11ycrawler against test course..."
paver pa11ycrawler

echo "Generating coverage report..."
paver pa11ycrawler_coverage
