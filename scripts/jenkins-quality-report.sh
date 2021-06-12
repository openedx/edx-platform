#!/usr/bin/env bash
set -e

# This script is used by the edx-platform-quality-check jenkins job.
source scripts/jenkins-common.sh
source scripts/thresholds.sh

# Run quality task. Pass in the 'fail-under' percentage to diff-quality
echo "Generating quality report."
mkdir -p test_root/log/
LOG_PREFIX=test_root/log/run_quality

paver run_quality 2> $LOG_PREFIX.err.log > $LOG_PREFIX.out.log
