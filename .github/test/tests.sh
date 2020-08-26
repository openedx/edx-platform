#!/usr/bin/env bash
set -x

cd /openedx/edx-platform

# Install required edx-ora2 for tests
#pip3 install -e git+https://github.com/fdns/edx-ora2.git@810e75fb2028272c10b3b86b645720c3e584a4c6#egg=ora2
pip3 install -e git+https://github.com/edx/edx-ora2.git@2.7.6#egg=ora2==2.7.6

# Test EOL Modifications

# Task Helper modifications for uchileedxlogin package
## Test before installing the package
DJANGO_SETTINGS_MODULE=lms.envs.test EDXAPP_TEST_MONGO_HOST=mongodb pytest \
	lms/djangoapps/instructor_task/tests/test_tasks_helper.py \
	lms/djangoapps/instructor_analytics/tests/test_basic.py \
	lms/djangoapps/certificates/tests/test_webview_views.py \
	lms/djangoapps/bulk_email/tests/ \
	lms/djangoapps/instructor/tests/
#DJANGO_SETTINGS_MODULE=lms.envs.test EDXAPP_TEST_MONGO_HOST=mongodb pytest lms/djangoapps/bulk_email/tests/ lms/djangoapps/instructor/tests/
#DJANGO_SETTINGS_MODULE=lms.envs.test EDXAPP_TEST_MONGO_HOST=mongodb pytest lms/djangoapps/bulk_email/tests/test_models_eol.py lms/djangoapps/instructor/tests/test_api_eol.py
## Test after installing the package
#pip3 install -e git+https://github.com/eol-uchile/uchileedxlogin@2db9adab2a3662ae04754cc158af57f2f197c236#egg=uchileedxlogin
#DJANGO_SETTINGS_MODULE=lms.envs.test EDXAPP_TEST_MONGO_HOST=mongodb pytest lms/djangoapps/instructor_task/tests/test_tasks_helper.py lms/djangoapps/instructor_analytics/tests/test_basic.py

