#!/bin/bash -e
. /edx/app/edxapp/edxapp_env
. /edx/app/edxapp/nodeenvs/edxapp/bin/activate
. /edx/app/edxapp/venvs/edxapp/bin/activate

cd /edx/app/edxapp/edx-platform

paver i18n_clean
make clean
git clean -fdx > /dev/null 2>&1
