"""
Settings to run LMS in devstack using optimized static assets.

This configuration changes LMS to use the optimized static assets generated for testing,
rather than picking up the files directly from the source tree.

The following Paver command can be used to run LMS in optimized mode:

  paver devstack lms --optimized

You can also generate the assets explicitly and then run Studio:

  paver update_assets lms --settings=test_static_optimized
  paver devstack lms --settings=devstack_optimized --fast

Note that changes to JavaScript assets will not be picked up automatically
as they are for non-optimized devstack. Instead, update_assets must be
invoked each time that changes have been made.
"""

########################## Devstack settings ###################################

from .devstack import *  # pylint: disable=wildcard-import, unused-wildcard-import

TEST_ROOT = REPO_ROOT / "test_root"  # pylint: disable=no-value-for-parameter

############################ STATIC FILES #############################

# Enable debug so that static assets are served by Django
DEBUG = True

#  Serve static files at /static directly from the staticfiles directory under test root.
# Note: optimized files for testing are generated with settings from test_static_optimized
STATIC_URL = "/static/"
STATICFILES_FINDERS = (
    'staticfiles.finders.FileSystemFinder',
)
STATICFILES_DIRS = (
    (TEST_ROOT / "staticfiles" / "lms").abspath(),
)
