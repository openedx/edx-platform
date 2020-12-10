#!/usr/bin/env bash

function show_help() {
    echo ""
    echo "Run all Edx tests including CMS, LMS and lib. Generate coverage reports"
    echo "in XML and HTML format. Create junit-xml and diff-cover reports as well."
    echo "Usage:"
    echo "      ./adg/pipelines/scripts/edx-run-test.sh [branch-name]"
    echo "Options:"
    echo "      -h,     help                Print usage information"
    echo "              branch-name         Branch name for diff-cover [default: origin/master]"
    echo "Example:"
    echo "      ./adg/pipelines/scripts/edx-run-test.sh origin/develop"
    echo ""
}

if [ "$1" == "-h" ]; then
    show_help
    exit 0
fi

set -e
set -o pipefail

FAIL_UNDER=80
branch="$1"

# There is no need to install the prereqs, as this was already
# just done via the dependencies override section of circle.yml.
export NO_PREREQ_INSTALL='true'

# run Edx common lib unit tests
paver test_lib --cov-args="-p" --skip-clean --cov-config=.coveragerc-local --cov-append

# run all Edx cms tests
paver test_system -s cms --cov-args="-p" --skip-clean --cov-config=.coveragerc-local --cov-append

# run all Edx lms tests
paver test_system -s lms --cov-args="-p" --skip-clean --cov-config=.coveragerc-local --cov-append

coverage xml --rcfile=.coveragerc-local
coverage html --rcfile=.coveragerc-local

echo "*** Generating diff-cover report ***"
EXIT_CODE=0
DIFF_COVER_REPORT=$(diff-cover reports/coverage.xml --compare-branch="${branch=origin/master}" \
    --html-report reports/diff_coverage.html --fail-under="$FAIL_UNDER") || EXIT_CODE=$?
export DIFF_COVER_REPORT
# post comment to PR only from circleci
[[ "$CIRCLECI" ]] && python3 adg/pipelines/scripts/post_comment.py -t Edx -s $EXIT_CODE
exit $EXIT_CODE
