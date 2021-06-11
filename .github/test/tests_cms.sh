#!/usr/bin/env bash
set -x

cd /openedx/edx-platform

# Create test root folder, required for tests
mkdir -p test_root/log/

# Install required edx-ora2 for tests
#pip3 install -e git+https://github.com/fdns/edx-ora2.git@810e75fb2028272c10b3b86b645720c3e584a4c6#egg=ora2
pip3 install ora2==2.11.5.1

# Test given parameter
EDXAPP_TEST_MONGO_HOST=mongodb python -Wd -m pytest --ds=cms.envs.test --junitxml=/openedx/edx-platform/reports/cms/nosetests.xml $1