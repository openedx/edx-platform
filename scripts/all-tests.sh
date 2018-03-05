#!/usr/bin/env bash
set -e

###############################################################################
#
#   all-tests.sh
#
#   Execute tests for edx-platform. This script is designed to be the
#   entry point for various CI systems.
#
###############################################################################

# Violations thresholds for failing the build
source scripts/thresholds.sh

XSSLINT_THRESHOLDS=`cat scripts/xsslint_thresholds.json`
export XSSLINT_THRESHOLDS=${XSSLINT_THRESHOLDS//[[:space:]]/}

if [ -n "$JENKINS_HOME" ] ; then
    source scripts/jenkins-common.sh
fi

scripts/generic-ci-tests.sh
