#!/usr/bin/env bash
set -e
set -vx


# Run this with: bash scripts/test_coverage.sh

# Clean up previous builds
git clean -qxfd
paver install_prereqs
rm -rf ../reports_*

export COVERAGE_DEBUG_FILE=reports/coverage_debug.log
export DISABLE_MIGRATIONS=1
export NO_PREREQ_INSTALL=1

counter=0
LIMIT=20

while [ "$counter" -lt "$LIMIT" ]
do
  DISABLE_MIGRATIONS=1 paver test_system -s lms --attr='!shard' --with-flaky --processes=-1 --cov-args="-p" --with-xunitmp
  mv reports "../reports_$counter"
  counter=`expr $counter + 1`
done
