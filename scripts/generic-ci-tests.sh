#!/usr/bin/env bash
set -exv

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
#       using the nose'attr' decorator (e.g. "@attr('shard_1')"). Anything with
#       the 'shard_n' attribute will run in the nth shard. If there isn't a
#       shard explicitly assigned, the test will run in the last shard (the one
#       with the highest number).
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

case "$TEST_SUITE" in

    "quality")
        echo "git log -1 --pretty=one"
        git log -1 --pretty=one

        echo "Finding fixme's and storing report..."
        paver find_fixme > fixme.log || { cat fixme.log; EXIT=1; }

        echo "[DEBUG] INSTALLED: "
        cat .prereqs_cache/Python_uninstall.sha1; echo ""
        cat .prereqs_cache/Python_prereqs.sha1; echo ""
        pip show edx-oauth2-provider
        pip show django-oauth-toolkit

        echo "Finding pep8 violations and storing report..."
        paver run_pep8 > pep8.log || { cat pep8.log; EXIT=1; }

        echo "[DEBUG] INSTALLED: "
        cat .prereqs_cache/Python_uninstall.sha1; echo ""
        cat .prereqs_cache/Python_prereqs.sha1; echo ""
        pip show edx-oauth2-provider
        pip show django-oauth-toolkit

        exit $EXIT
        ;;

    *)
        echo "git log -1 --pretty=one"
        git log -1 --pretty=one

        paver install_prereqs

        echo "[DEBUG] INSTALLED: "
        cat .prereqs_cache/Python_uninstall.sha1; echo ""
        cat .prereqs_cache/Python_prereqs.sha1; echo ""
        pip show edx-oauth2-provider
        pip show django-oauth-toolkit
        ;;
esac
