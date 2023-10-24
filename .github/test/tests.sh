#!/usr/bin/env bash
set -x

cd /openedx/edx-platform

# Create test root folder, required for tests
mkdir -p test_root/log/

# Install required edx-ora2 for tests
pip3 install ora2==2.11.5.1

# Test EOL Modifications

# Task Helper modifications for uchileedxlogin package
## Test before installing the package
DJANGO_SETTINGS_MODULE=lms.envs.test EDXAPP_TEST_MONGO_HOST=mongodb pytest --exitfirst --full-trace --verbose \
	lms/djangoapps/instructor_task/tests/test_tasks_helper.py \
	lms/djangoapps/instructor_analytics/tests/test_basic.py \
	lms/djangoapps/certificates/tests/test_webview_views.py \
	lms/djangoapps/bulk_email/tests/ \
	lms/djangoapps/instructor/tests/
