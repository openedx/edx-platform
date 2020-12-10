#!/usr/bin/env bash
set -e
set -o pipefail

function show_help() {
    echo ""
    echo "Run all ADG tests inside openedx/adg/ including CMS, LMS and common. Generate coverage reports"
    echo "in XML and HTML format. Create junit-xml and diff-cover reports as well."
    echo "Usage:"
    echo "      ./adg/pipelines/scripts/adg-run-test.sh [branch-name]"
    echo "Options:"
    echo "      -h,     help                Print usage information"
    echo "              branch-name         Branch name for diff-cover [default: origin/master]"
    echo "Example:"
    echo "      ./adg/pipelines/scripts/adg-run-test.sh origin/develop"
    echo ""
}

if [ "$1" == "-h" ]; then
    show_help
    exit 0
fi

readonly LMS=lms
readonly CMS=cms
FAIL_UNDER=80

function run_adg_test() {
    echo "========================================"
    echo "Running ADG specific tests for ${1}"
    echo "========================================"
    EXIT_CODE=0
    # Run ADG tests and create (or append) coverage. Generate xml and html coverage files
    python -Wd -m pytest --ds="$1".envs.test --junitxml=reports/"$1"/adg-nosetests.xml \
        openedx/adg/"$1" openedx/adg/common --cov --cov-config=setup.cfg --cov-config=tox.ini \
        --cov-config=adg/pipelines/.coveragerc-adg --cov-report xml --cov-report html $2 || EXIT_CODE=1
    echo "${1}_exit_code=$EXIT_CODE"
    return $EXIT_CODE
}

function generate_diff_cover_report() {
    echo "*** Generating diff-cover report ***"
    # Run ADG tests and create (or append) .coverage file
    EXIT_CODE=0
    DIFF_COVER_REPORT=$(diff-cover reports/coverage.xml --compare-branch="$1" \
        --html-report reports/diff_coverage.html --fail-under="${2:-80}") || EXIT_CODE=1
    export DIFF_COVER_REPORT
    # post comment to PR only from circleci
    [[ "$CIRCLECI" ]] && python3 adg/pipelines/scripts/post_comment.py -t ADG -s $EXIT_CODE
    echo "$DIFF_COVER_REPORT"
    echo "The exit code for coverage report is $EXIT_CODE"
    return $EXIT_CODE
}

BRANCH="${1:-origin/master}"
[[ "$BRANCH" != origin/* ]] && echo "Invalid branch name. It must start with origin/..." && exit 1

rm -rf reports                                      # First delete previous reports
declare -i ERROR_COUNT=0                            # The count of, no of commands failed
run_adg_test $LMS || ERROR_COUNT+=$?                # Run test for LMS and LMS common
run_adg_test $CMS "--cov-append" || ERROR_COUNT+=$? # Run test for CMS and CMS common

if [[ -z "$CIRCLECI" || ("$CIRCLECI" && ("$BRANCH" != "origin/master")) ]]; then

    if [[ ($ERROR_COUNT -eq 0) ]]; then
        # Generate report only if we are running test and coverage for ADG only
        generate_diff_cover_report "$BRANCH" $FAIL_UNDER || ERROR_COUNT+=$?
    fi

    echo "The error count is $ERROR_COUNT"
    if [[ $ERROR_COUNT -gt 0 ]]; then exit 1; else exit 0; fi
fi
