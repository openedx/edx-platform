#!/usr/bin/env bash
set -e

###############################################################################
#
# DO NOT MERGE THIS
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
    PAVER_ARGS="-v --django_version=1.11"
else
    PAVER_ARGS="-v"
fi
PARALLEL="--processes=-1"
export SUBSET_JOB=$JOB_NAME
case "$TEST_SUITE" in

    "*")
        echo "Doing nothing"
        paver --help

        mkdir -p reports

        # Need to create an empty test result so the post-build
        # action doesn't fail the build.
        emptyxunit "quality"
        exit 0
        ;;
esac
