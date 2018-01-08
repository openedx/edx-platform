#!/usr/bin/env bash
set -e

###############################################################################
#
#   generic-ci-tests.sh
#
#   Execute all tests for edx-platform.
#
#   This script can be called from CI jobs that define
#   these environment variables:
#
#   `TEST_SUITE` defines which kind of test to run.
#   Possible values are:
#
#       - "quality": Run the quality (pep8/pylint) checks
#       - "lms-unit": Run the LMS Python unit tests
#       - "cms-unit": Run the CMS Python unit tests
#       - "js-unit": Run the JavaScript tests
#       - "commonlib-unit": Run Python unit tests from the common/lib directory
#       - "commonlib-js-unit": Run the JavaScript tests and the Python unit
#           tests from the common/lib directory
#       - "lms-acceptance": Run the acceptance (Selenium/Lettuce) tests for
#           the LMS
#       - "cms-acceptance": Run the acceptance (Selenium/Lettuce) tests for
#           Studio
#       - "bok-choy": Run acceptance tests that use the bok-choy framework
#
#   `SHARD` is a number indicating which subset of the tests to build.
#
#       For "bok-choy" and "lms-unit", the tests are put into shard groups
#       using the 'attr' decorator (e.g. "@attr(shard=1)"). Anything with
#       the 'shard=n' attribute will run in the nth shard. If there isn't a
#       shard explicitly assigned, the test will run in the last shard.
#
#   Jenkins-specific configuration details:
#
#   - The edx-platform git repository is checked out by the Jenkins git plugin.
#   - Jenkins logs in as user "jenkins"
#   - The Jenkins file system root is "/home/jenkins"
#   - An init script creates a virtualenv at "/home/jenkins/edx-venv"
#     with some requirements pre-installed (such as scipy)
#
#  Jenkins worker setup:
#  See the edx/configuration repo for Jenkins worker provisioning scripts.
#  The provisioning scripts install requirements that this script depends on!
#
###############################################################################

# If the environment variable 'SHARD' is not set, default to 'all'.
# This could happen if you are trying to use this script from
# jenkins and do not define 'SHARD' in your multi-config project.
# Note that you will still need to pass a value for 'TEST_SUITE'
# or else no tests will be executed.
SHARD=${SHARD:="all"}
NUMBER_OF_BOKCHOY_THREADS=${NUMBER_OF_BOKCHOY_THREADS:=1}

# Clean up previous builds
git clean -qxfd

function emptyxunit {

    cat > reports/$1.xml <<END
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="$1" tests="1" errors="0" failures="0" skip="0">
<testcase classname="$1" name="$1" time="0.604"></testcase>
</testsuite>
END

}

if [[ $DJANGO_VERSION == '1.11' ]]; then
    TOX="tox -e py27-django111 --"
elif [[ $DJANGO_VERSION == '1.10' ]]; then
    TOX="tox -e py27-django110 --"
elif [[ $DJANGO_VERSION == '1.9' ]]; then
    TOX="tox -e py27-django19 --"
else
    TOX=""
fi
PAVER_ARGS="-v"
PARALLEL="--processes=-1"
export SUBSET_JOB=$JOB_NAME

function run_paver_quality {
    QUALITY_TASK=$1
    shift
    mkdir -p test_root/log/
    LOG_PREFIX=test_root/log/$QUALITY_TASK
    $TOX paver $QUALITY_TASK $* 2> $LOG_PREFIX.err.log > $LOG_PREFIX.out.log || {
        echo "STDOUT (last 100 lines of $LOG_PREFIX.out.log):";
        tail -n 100 $LOG_PREFIX.out.log;
        echo "STDERR (last 100 lines of $LOG_PREFIX.err.log):";
        tail -n 100 $LOG_PREFIX.err.log;
        return 1;
    }
    return 0;
}

case "$TEST_SUITE" in

    "quality")
        # echo "Finding fixme's and storing report..."
        # run_paver_quality find_fixme || EXIT=1

        # echo "Finding pep8 violations and storing report..."
        # run_paver_quality run_pep8 || EXIT=1
        echo "Finding pylint violations and storing in report..."
        run_paver_quality run_pylint -l $LOWER_PYLINT_THRESHOLD:$UPPER_PYLINT_THRESHOLD || EXIT=1

        # mkdir -p reports

        # echo "Finding ESLint violations and storing report..."
        # run_paver_quality run_eslint -l $ESLINT_THRESHOLD || EXIT=1
        # echo "Finding Stylelint violations and storing report..."
        # run_paver_quality run_stylelint -l $STYLELINT_THRESHOLD || EXIT=1
        # echo "Running code complexity report (python)."
        # run_paver_quality run_complexity || echo "Unable to calculate code complexity. Ignoring error."
        # echo "Running xss linter report."
        # run_paver_quality run_xsslint -t $XSSLINT_THRESHOLDS || EXIT=1
        # echo "Running safe commit linter report."
        # run_paver_quality run_xsscommitlint || EXIT=1
        # # Run quality task. Pass in the 'fail-under' percentage to diff-quality
        # echo "Running diff quality."
        # run_paver_quality run_quality -p 100 -l $LOWER_PYLINT_THRESHOLD:$UPPER_PYLINT_THRESHOLD || EXIT=1

        # Need to create an empty test result so the post-build
        # action doesn't fail the build.
        emptyxunit "quality"
        exit $EXIT
        ;;

esac
