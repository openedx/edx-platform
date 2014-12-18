#!/usr/bin/env bash
set -ev

# Violations thresholds for failing the build
PYLINT_THRESHOLD=3600
PEP8_THRESHOLD=0

case "${TEST_SUITE}" in

    "quality")
        paver find_fixme > fixme.log
        paver run_pep8 -l $PEP8_THRESHOLD > pep8.log
        paver run_pylint -l $PYLINT_THRESHOLD > pylint.log
        # Run quality task. Pass in the 'fail-under' percentage to diff-quality
        paver run_quality -p 100
        ;;

    "unit-cms")
        paver test_system -s cms --fasttest
        ;;

    "unit-lms")
        paver test_system -s lms --fasttest
        ;;

    "unit-lib")
        paver test_lib
        ;;

    "unit-js")
        paver test_js
        ;;

    *)
        echo "${TEST_SUITE}"
        ;;
esac
