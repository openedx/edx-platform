"""
Settings used when generating static assets for use in tests.

Bok Choy uses two different settings files:
1. test_static_optimized is used when invoking collectstatic
2. bok_choy is used when running CMS and LMS

Note: it isn't possible to have a single settings file, because Django doesn't
support both generating static assets to a directory and also serving static
from the same directory.

"""

import os
from path import path  # pylint: disable=no-name-in-module

# Pylint gets confused by path.py instances, which report themselves as class
# objects. As a result, pylint applies the wrong regex in validating names,
# and throws spurious errors. Therefore, we disable invalid-name checking.
# pylint: disable=invalid-name


########################## Prod-like settings ###################################
# These should be as close as possible to the settings we use in production.
# As in prod, we read in environment and auth variables from JSON files.
# Unlike in prod, we use the JSON files stored in this repo.
# This is a convenience for ensuring (a) that we can consistently find the files
# and (b) that the files are the same in Jenkins as in local dev.
os.environ['SERVICE_VARIANT'] = 'bok_choy'
os.environ['CONFIG_ROOT'] = path(__file__).abspath().dirname()  # pylint: disable=no-value-for-parameter

from .aws import *  # pylint: disable=wildcard-import, unused-wildcard-import

######################### Testing overrides ####################################

# Redirects to the test_root folder within the repo
TEST_ROOT = REPO_ROOT / "test_root"  # pylint: disable=no-value-for-parameter
LOG_DIR = (TEST_ROOT / "log").abspath()

# Stores the static files under test root so that they don't overwrite existing static assets
STATIC_ROOT = (TEST_ROOT / "staticfiles" / "lms").abspath()

# Disables uglify when tests are running (used by build.js).
# 1. Uglify is by far the slowest part of the build process
# 2. Having full source code makes debugging tests easier for developers
os.environ['REQUIRE_BUILD_PROFILE_OPTIMIZE'] = 'none'
PIPELINE_JS_COMPRESSOR = None
