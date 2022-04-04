#!/usr/bin/env bash
set -e

###############################################################################
#
#   accessibility-tests.sh
#
#   Execute the accessibility tests for edx-platform.
#
#   If the optional `TOX_ENV` environment variable is defined, it
#   specifies which version of Python and Django should be installed when
#   running the tests inside a `tox` virtualenv.  If undefined, the tests are
#   run using the currently active Python environment. For more information
#   on what versions are supported, check the tox.ini file.
#
###############################################################################

echo "Setting up for accessibility tests..."
source scripts/jenkins-common.sh

# if specified tox environment is supported, prepend paver commands
# with tox env invocation
if [ -z ${TOX_ENV+x} ] || [[ ${TOX_ENV} == 'null' ]]; then
    TOX=""
elif tox -l |grep -q "${TOX_ENV}"; then
    TOX="tox -r -e ${TOX_ENV} --"
else
    echo "${TOX_ENV} is not currently supported. Please review the"
    echo "tox.ini file to see which environments are supported"
    exit 1
fi

echo "Running explicit accessibility tests..."
SELENIUM_BROWSER=chrome BOKCHOY_HEADLESS=true $TOX paver test_a11y
