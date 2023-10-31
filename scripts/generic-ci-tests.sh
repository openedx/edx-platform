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
#       - "quality": Run the quality (pycodestyle/pylint) checks
#       - "lms-unit": Run the LMS Python unit tests
#       - "cms-unit": Run the CMS Python unit tests
#       - "js-unit": Run the JavaScript tests
#       - "pavelib-unit": Run Python unit tests from the pavelib/lib directory
#       - "pavelib-js-unit": Run the JavaScript tests and the Python unit
#           tests from the pavelib/lib directory
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

# Clean up previous builds
git clean -qxfd

function emptyxunit {

    cat > "reports/$1.xml" <<END
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="$1" tests="1" errors="0" failures="0" skip="0">
<testcase classname="pavelib.quality" name="$1" time="0.604"></testcase>
</testsuite>
END

}

# if specified tox environment is supported, prepend paver commands
# with tox env invocation
if [ -z ${TOX_ENV+x} ] || [[ ${TOX_ENV} == 'null' ]]; then
    echo "TOX_ENV: ${TOX_ENV}"
    TOX=""
elif tox -l |grep -q "${TOX_ENV}"; then
    if [[ "${TOX_ENV}" == 'quality' ]]; then
        TOX=""
    else
        TOX="tox -r -e ${TOX_ENV} --"
    fi
else
    echo "${TOX_ENV} is not currently supported. Please review the"
    echo "tox.ini file to see which environments are supported"
    exit 1
fi

PAVER_ARGS="-v"
export SUBSET_JOB=$JOB_NAME

function run_paver_quality {
    QUALITY_TASK=$1
    shift
    mkdir -p test_root/log/
    LOG_PREFIX="test_root/log/$QUALITY_TASK"
    $TOX paver "$QUALITY_TASK" "$@" 2> "$LOG_PREFIX.err.log" > "$LOG_PREFIX.out.log" || {
        echo "STDOUT (last 100 lines of $LOG_PREFIX.out.log):";
        tail -n 100 "$LOG_PREFIX.out.log"
        echo "STDERR (last 100 lines of $LOG_PREFIX.err.log):";
        tail -n 100 "$LOG_PREFIX.err.log"
        return 1;
    }
    return 0;
}

case "$TEST_SUITE" in

    "quality")
        EXIT=0

        mkdir -p reports

        case "$SHARD" in
            1)
                echo "Finding pylint violations and storing in report..."
                run_paver_quality run_pylint --system=common  || { EXIT=1; }
                ;;

            2)
                echo "Finding pylint violations and storing in report..."
                run_paver_quality run_pylint --system=lms || { EXIT=1; }
                ;;

            3)
                echo "Finding pylint violations and storing in report..."
                run_paver_quality run_pylint --system="cms,openedx,pavelib" || { EXIT=1; }
                ;;

            4)
                echo "Finding fixme's and storing report..."
                run_paver_quality find_fixme || { EXIT=1; }
                echo "Finding pycodestyle violations and storing report..."
                run_paver_quality run_pep8 || { EXIT=1; }
                echo "Finding ESLint violations and storing report..."
                run_paver_quality run_eslint -l "$ESLINT_THRESHOLD" || { EXIT=1; }
                echo "Finding Stylelint violations and storing report..."
                run_paver_quality run_stylelint || { EXIT=1; }
                echo "Running xss linter report."
                run_paver_quality run_xsslint -t "$XSSLINT_THRESHOLDS" || { EXIT=1; }
                echo "Running PII checker on all Django models..."
                run_paver_quality run_pii_check || { EXIT=1; }
                echo "Running reserved keyword checker on all Django models..."
                run_paver_quality check_keywords || { EXIT=1; }
                ;;

        esac

        # Need to create an empty test result so the post-build
        # action doesn't fail the build.
        emptyxunit "stub"
        exit "$EXIT"
        ;;

    "js-unit")
        $TOX paver test_js --coverage
        $TOX paver diff_coverage
        ;;

    "pavelib-js-unit")
        EXIT=0
        $TOX paver test_js --coverage --skip-clean || { EXIT=1; }
        paver test_lib --skip-clean $PAVER_ARGS || { EXIT=1; }

        # This is to ensure that the build status of the shard is properly set.
        # Because we are running two paver commands in a row, we need to capture
        # their return codes in order to exit with a non-zero code if either of
        # them fail. We put the || clause there because otherwise, when a paver
        # command fails, this entire script will exit, and not run the second
        # paver command in this case statement. So instead of exiting, the value
        # of a variable named EXIT will be set to 1 if either of the paver
        # commands fail. We then use this variable's value as our exit code.
        # Note that by default the value of this variable EXIT is not set, so if
        # neither command fails then the exit command resolves to simply exit
        # which is considered successful.
        exit "$EXIT"
        ;;
esac
