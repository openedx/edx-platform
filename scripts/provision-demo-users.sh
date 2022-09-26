#!/usr/bin/env bash

# Usage:
#   In an LMS-enabled container,
#   from the directory /edx/app/edxapp/edx-platform, run:
#     ./scripts/provision-demo-users.sh
#
# This file is an experimental re-implementation of demo user provisioning
# process defined in this Ansible role:
# https://github.com/openedx/configuration/tree/master/playbooks/roles/demo
#
# It provisions five users:
#  * edx (global superuser)
#  * staff (global staff)
#  * verified
#  * audit
#  * honor
# Each of which has {username}@example.com as their email and 'edx' as their password.
#
# It was written as part of the effort to move our dev tools off of Ansible and
# Paver, described here: https://github.com/openedx/devstack/pull/866
# TODO: If the effort described above is abandoned, then this script should
# probably be deleted.

set -xeuo pipefail

DEMO_COURSE_KEY='course-v1:edX+DemoX+Demo_Course'

# Hash of 'edx' password.
DEMO_PASSWORD_HASH='pbkdf2_sha256$20000$TjE34FJjc3vv$0B7GUmH8RwrOc/BvMoxjb5j8EgnWTt3sxorDANeF7Qw='

# Create users (if they don't exist) and set passwords.
# 'password_is_edx' is purposefully unquoted so that it expands into two arguments.
password_is_edx="--initial-password-hash $DEMO_PASSWORD_HASH"
./manage.py lms manage_user edx      edx@example.com      $password_is_edx --superuser
./manage.py lms manage_user staff    staff@example.com    $password_is_edx --staff
./manage.py lms manage_user verified verified@example.com $password_is_edx
./manage.py lms manage_user audit    audit@example.com    $password_is_edx
./manage.py lms manage_user honor    honor@example.com    $password_is_edx

# Enroll users in demo course.
for username in staff verified audit honor; do
	./manage.py lms enroll_user_in_course -e "${username}@example.com" -c "$DEMO_COURSE_KEY"
done

# Seed the forums for the demo course.
./manage.py lms seed_permissions_roles "$DEMO_COURSE_KEY"
