#!/usr/bin/env bash

# Usage:
#   In a CMS-enabled container,
#   from the directory /edx/app/edxapp/edx-platform, run:
#     ./scripts/provision-demo-course.sh
#
# This file is an experimental re-implementation of demo course provisioning
# process defined in this Ansible role:
# https://github.com/openedx/configuration/tree/master/playbooks/roles/demo
#
# It was written as part of the effort to move our dev tools off of Ansible and
# Paver, described here: https://github.com/openedx/devstack/pull/866
# TODO: If the effort described above is abandoned, then this script should
# probably be deleted.

set -xeuo pipefail

DEMO_COURSE_KEY='course-v1:edX+DemoX+Demo_Course'

# Delete the demo course clone (if it exists) and then do a shallow re-clone of it.
mkdir -p /edx/app/demo
(
	cd /edx/app/demo &&
	rm -rf edx-demo-course &&
	git clone https://github.com/openedx/openedx-demo-course.git --depth 1
)

# Import the course.
./manage.py cms import /edx/var/edxapp/data /edx/app/demo/edx-demo-course

