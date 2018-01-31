#!/usr/bin/env bash
set -e

###############################################################################
#
#   accessibility-tests.sh
#
#   Execute the accessibility tests for edx-platform.
#
#   If the optional `DJANGO_VERSION` environment variable is defined, it
#   specifies which version of Django should be installed when running the
#   tests inside a `tox` virtualenv.  If undefined, the tests are run using
#   the currently active Python environment.
#
###############################################################################

if [[ $DJANGO_VERSION == '1.11' ]]; then
    TOX="tox -r -e py27-django111 --"
elif [[ $DJANGO_VERSION == '1.10' ]]; then
    TOX="tox -r -e py27-django110 --"
elif [[ $DJANGO_VERSION == '1.9' ]]; then
    TOX="tox -r -e py27-django19 --"
else
    TOX=""
fi


echo "Setting up for accessibility tests..."
source scripts/jenkins-common.sh

echo "Running explicit accessibility tests..."
SELENIUM_BROWSER=phantomjs $TOX paver test_a11y

# The settings that we use are installed with the pa11ycrawler module
export SCRAPY_SETTINGS_MODULE='pa11ycrawler.settings'

echo "Running pa11ycrawler against test course..."
$TOX paver pa11ycrawler --fasttest --skip-clean --fetch-course --with-html
