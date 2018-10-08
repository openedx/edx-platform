#!/bin/bash

source /edx/app/edxapp/edxapp_env
cd /edx/app/edxapp/edx-platform
if [ -d /edx/app/edxapp/edx-platform/unittest_reports ]; then
    true
else
    mkdir -p /edx/app/edxapp/edx-platform/unittest_reports
fi
if [ -d /edx/app/edxapp/edx-platform/unittest_reports/nosetests ]; then
    true
else
    mkdir -p /edx/app/edxapp/edx-platform/unittest_reports/nosetests
fi
if [ -d /edx/app/edxapp/edx-platform/unittest_reports/coverage ]; then
    true
else
    mkdir -p /edx/app/edxapp/edx-platform/unittest_reports/coverage
fi
find /edx/app/edxapp/edx-platform/unittest_reports -type f -delete
paver test_system -s lms "--cov-report=xml reports/"
cp /edx/app/edxapp/edx-platform/reports/lms/nosetests.xml /edx/app/edxapp/edx-platform/unittest_reports/nosetests/lmsnosetests.xml
cp /edx/app/edxapp/edx-platform/reports/coverage.xml /edx/app/edxapp/edx-platform/unittest_reports/coverage/lmscoverage.xml
paver test_system -s cms "--cov-report=xml reports/"
cp /edx/app/edxapp/edx-platform/reports/cms/nosetests.xml /edx/app/edxapp/edx-platform/unittest_reports/nosetests/cmsnosetests.xml
cp /edx/app/edxapp/edx-platform/reports/coverage.xml /edx/app/edxapp/edx-platform/unittest_reports/coverage/cmscoverage.xml
paver test_lib "--cov-report=xml reports/"
cp /edx/app/edxapp/edx-platform/reports/common/nosetests.xml /edx/app/edxapp/edx-platform/unittest_reports/nosetests/commonnosetests.xml
cp /edx/app/edxapp/edx-platform/reports/coverage.xml /edx/app/edxapp/edx-platform/unittest_reports/coverage/commoncoverage.xml