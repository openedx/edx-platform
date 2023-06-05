#!/usr/bin/env bash
#
# Context: docs/decisions/0007-sys-path-modification-removal.rst
#
# Usage:
#
#      ~/edx-platform> import_shims/regenerate_current_shims.sh
#
# This script, on its own, should remove and re-generate the import shims as currently
# reflected in master.
# 
# Last run by Kyle McCormick (@kdmccormick) 2020-11-18

rm -rf import_shims/lms
rm -rf import_shims/studio

# Support old-style lms/djangoapps imports in LMS.
import_shims/generate_shims.sh lms/djangoapps import_shims/lms

# Support old-style cms/djangoapps imports in Studio.
import_shims/generate_shims.sh cms/djangoapps import_shims/studio

# Support old-style common/djangoapps imports LMS and Studio.
import_shims/generate_shims.sh common/djangoapps import_shims/lms
import_shims/generate_shims.sh common/djangoapps import_shims/studio
