#!/usr/bin/env bash
set -e

###############################################################################
#
#   edx-all-tests.sh
#
#   Execute all tests for edx-platform.
#
#   This script can be called from a Jenkins
#   multiconfiguration job that defines these environment
#   variables:
#
#   `TEST_SUITE` defines which kind of test to run.
#   Possible values are:
#
#       - "quality": Run the quality (pep8/pylint) checks
#       - "unit": Run the JavaScript and Python unit tests
#            (also tests building the Sphinx documentation,
#             because we couldn't think of a better place to put it)
#       - "lms-acceptance": Run the acceptance (Selenium) tests for the LMS
#       - "cms-acceptance": Run the acceptance (Selenium) tests for Studio
#       - "bok-choy": Run acceptance tests that use the bok-choy framework
#
#   `SHARD` is a number (1, 2, or 3) indicating which subset of the tests
#       to build.  Currently, "lms-acceptance" and "bok-choy" each have two
#       shards (1 and 2), "cms-acceptance" has three shards (1, 2, and 3),
#       and all the other test suites have one shard.
#
#       For the "bok-choy", the tests are put into shard groups using the nose
#       'attr' decorator (e.g. "@attr('shard_1')").  Currently, anything with
#       the 'shard_1' attribute will run in the first shard.  All other bok-choy
#       tests will run in shard 2.
#
#       For the lettuce acceptance tests, ("lms-" and "cms-acceptance") they
#       are decorated with "@shard_{}" (e.g. @shard_1 for the first shard).
#       The lettuce tests must have a shard specified to be run in jenkins,
#       as there is no shard that runs unspecified tests.
#
#
#   Jenkins configuration:
#
#   - The edx-platform git repository is checked out by the Jenkins git plugin.
#
#   - Jenkins logs in as user "jenkins"
#
#   - The Jenkins file system root is "/home/jenkins"
#
#   - An init script creates a virtualenv at "/home/jenkins/edx-venv"
#     with some requirements pre-installed (such as scipy)
#
#  Jenkins worker setup:
#  See the edx/configuration repo for Jenkins worker provisioning scripts.
#  The provisioning scripts install requirements that this script depends on!
#
###############################################################################

# Clean up previous builds
git clean -qxfd

source scripts/jenkins-common.sh

# Violations thresholds for failing the build
PYLINT_THRESHOLD=5500

# If the environment variable 'SHARD' is not set, default to 'all'.
# This could happen if you are trying to use this script from
# jenkins and do not define 'SHARD' in your multi-config project.
# Note that you will still need to pass a value for 'TEST_SUITE'
# or else no tests will be executed.
SHARD=${SHARD:="all"}

case "$TEST_SUITE" in

    "quality")
        echo "Finding fixme's and storing report..."
        paver find_fixme > fixme.log || { cat fixme.log; EXIT=1; }
        echo "Finding pep8 violations and storing report..."
        paver run_pep8 > pep8.log || { cat pep8.log; EXIT=1; }
        echo "Finding pylint violations and storing in report..."
        paver run_pylint -l $PYLINT_THRESHOLD > pylint.log || { cat pylint.log; EXIT=1; }
        # Run quality task. Pass in the 'fail-under' percentage to diff-quality
        paver run_quality -p 100

        mkdir -p reports
        paver run_complexity > reports/code_complexity.log || echo "Unable to calculate code complexity. Ignoring error."
        # Need to create an empty test result so the post-build
        # action doesn't fail the build.
        cat > reports/quality.xml <<END
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="quality" tests="1" errors="0" failures="0" skip="0">
<testcase classname="quality" name="quality" time="0.604"></testcase>
</testsuite>
END
        exit $EXIT
        ;;

    "unit")
        case "$SHARD" in
            "lms")
                paver test_system -s lms --extra_args="--with-flaky" || { EXIT=1; }
                paver coverage
                ;;
            "cms-js-commonlib")
                paver test_system -s cms --extra_args="--with-flaky" || { EXIT=1; }
                paver test_js --coverage --skip_clean || { EXIT=1; }
                paver test_lib --skip_clean --extra_args="--with-flaky" || { EXIT=1; }
                paver coverage
                ;;
            *)
                paver test --extra_args="--with-flaky"
                paver coverage
                ;;
        esac

        exit $EXIT
        ;;

    "lms-acceptance")
        case "$SHARD" in

            "all")
                paver test_acceptance -s lms --extra_args="-v 3"
                ;;

            "2")
                mkdir -p reports
                mkdir -p reports/acceptance
                cat > reports/acceptance/xunit.xml <<END
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="nosetests" tests="1" errors="0" failures="0" skip="0">
<testcase classname="lettuce.tests" name="shard_placeholder" time="0.001"></testcase>
</testsuite>
END
                ;;
            *)
                paver test_acceptance -s lms --extra_args="-v 3"
                ;;
        esac
        ;;

    "cms-acceptance")
        case "$SHARD" in

            "all"|"1")
                paver test_acceptance -s cms --extra_args="-v 3"
                ;;

            "2"|"3")
                mkdir -p reports/acceptance
                cat > reports/acceptance/xunit.xml <<END
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="nosetests" tests="1" errors="0" failures="0" skip="0">
<testcase classname="lettuce.tests" name="shard_placeholder" time="0.001"></testcase>
</testsuite>
END
                ;;

        esac
        ;;

    "bok-choy")
        case "$SHARD" in

            "all")
                paver test_bokchoy || { EXIT=1; }
                ;;

            "1")
                paver test_bokchoy --extra_args="-a shard_1 --with-flaky" || { EXIT=1; }
                ;;

            "2")
                paver test_bokchoy --extra_args="-a 'shard_2' --with-flaky" || { EXIT=1; }
                ;;

            "3")
                paver test_bokchoy --extra_args="-a 'shard_3' --with-flaky" || { EXIT=1; }
                ;;

            "4")
                paver test_bokchoy --extra_args="-a shard_1=False,shard_2=False,shard_3=False --with-flaky" || { EXIT=1; }
                ;;

            # Default case because if we later define another bok-choy shard on Jenkins
            # (e.g. Shard 5) in the multi-config project and expand this file
            # with an additional case condition, old branches without that commit
            # would not execute any tests on the worker assigned to that shard
            # and thus their build would fail.
            # This way they will just report 1 test executed and passed.
            *)
                # Need to create an empty test result so the post-build
                # action doesn't fail the build.
                # May be unnecessary if we changed the "Skip if there are no test files"
                # option to True in the jenkins job definitions.
                mkdir -p reports/bok_choy
                cat > reports/bok_choy/xunit.xml <<END
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="nosetests" tests="1" errors="0" failures="0" skip="0">
<testcase classname="acceptance.tests" name="shard_placeholder" time="0.001"></testcase>
</testsuite>
END
                ;;
        esac

        # Move the reports to a directory that is unique to the shard
        # so that when they are 'slurped' to the main flow job, they
        # do not conflict with and overwrite reports from other shards.
        mv reports/ reports_tmp/
        mkdir -p reports/${TEST_SUITE}/${SHARD}
        mv reports_tmp/* reports/${TEST_SUITE}/${SHARD}
        rm -r reports_tmp/
        exit $EXIT
        ;;

esac
