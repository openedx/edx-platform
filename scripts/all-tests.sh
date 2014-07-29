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

source $HOME/jenkins_env

# Clean up previous builds
git clean -qxfd

# Clear the mongo database
# Note that this prevents us from running jobs in parallel on a single worker.
mongo --quiet --eval 'db.getMongo().getDBNames().forEach(function(i){db.getSiblingDB(i).dropDatabase()})'

# Ensure we have fetched origin/master
# Some of the reporting tools compare the checked out branch to origin/master;
# depending on how the GitHub plugin refspec is configured, this may
# not already be fetched.
git fetch origin master:refs/remotes/origin/master

# Reset the jenkins worker's ruby environment back to
# the state it was in when the instance was spun up.
if [ -e $HOME/edx-rbenv_clean.tar.gz ]; then
    rm -rf $HOME/.rbenv
    tar -C $HOME -xf $HOME/edx-rbenv_clean.tar.gz
fi

# Bootstrap Ruby requirements so we can run the tests
bundle install

# Ensure the Ruby environment contains no stray gems
bundle clean --force

# Reset the jenkins worker's virtualenv back to the
# state it was in when the instance was spun up.
if [ -e $HOME/edx-venv_clean.tar.gz ]; then
    rm -rf $HOME/edx-venv
    tar -C $HOME -xf $HOME/edx-venv_clean.tar.gz
fi

# Activate the Python virtualenv
source $HOME/edx-venv/bin/activate

case "$TEST_SUITE" in

    "quality")
        paver run_pep8 > pep8.log || { cat pep8.log ; exit 1; }
        paver run_pylint > pylint.log || { cat pylint.log; exit 1; }
        paver run_quality

        # Need to create an empty test result so the post-build
        # action doesn't fail the build.
        mkdir -p reports
        cat > reports/quality.xml <<END
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="quality" tests="1" errors="0" failures="0" skip="0">
<testcase classname="quality" name="quality" time="0.604"></testcase>
</testsuite>
END
        ;;

    "unit")
        paver test
        paver coverage
        ;;

    "lms-acceptance")
        paver test_acceptance -s lms --extra_args="-v 3 --tag shard_${SHARD}"
        ;;

    "cms-acceptance")
        paver test_acceptance -s cms --extra_args="-v 3 --tag shard_${SHARD}"
        ;;

    "bok-choy")
        case "$SHARD" in
            "1")
                paver test_bokchoy --extra_args="-a shard_1"
                ;;

            "2")
                paver test_bokchoy --extra_args="-a '!shard_1'"
               ;;
        esac
        paver bokchoy_coverage
        ;;

esac
