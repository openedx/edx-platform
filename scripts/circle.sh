#!/usr/bin/env sh

case $CIRCLE_NODE_INDEX in
    0) paver test_lib --extra_args="--with-flaky" --cov_args="-p" ;;

    1) paver test_system -s cms --extra_args="--with-flaky --with-xunit" --cov_args="-p" ;;

    2) paver test_system -s lms --extra_args="--with-flaky --with-xunit" --cov_args="-p" ;;
esac

RET=$?

cp -r reports/. $CIRCLE_TEST_REPORTS

exit $RET
