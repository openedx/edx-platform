#!/usr/bin/env bash
set -e

# This script is used by the edx-platform-quality-check jenkins job.
source scripts/jenkins-common.sh
source scripts/thresholds.sh

# Run quality task. Pass in the 'fail-under' percentage to diff-quality
echo "Running diff quality."
mkdir -p test_root/log/
LOG_PREFIX=test_root/log/run_quality

if [[ $TARGET_BRANCH != origin/* ]]; then
    TARGET_BRANCH=origin/$TARGET_BRANCH
fi
paver run_quality -b $TARGET_BRANCH -p 100 -l $LOWER_PYLINT_THRESHOLD:$UPPER_PYLINT_THRESHOLD 2> $LOG_PREFIX.err.log > $LOG_PREFIX.out.log
