"""
Settings to run Studio in devstack using optimized static assets.

This configuration changes Studio to use the optimized static assets generated for testing,
rather than picking up the files directly from the source tree.

The following Paver command can be used to run Studio in optimized mode:

  paver devstack studio --optimized

You can also generate the assets explicitly and then run Studio:

  paver update_assets cms --settings=test_static_optimized
  paver devstack studio --settings=devstack_optimized --fast

Note that changes to JavaScript assets will not be picked up automatically
as they are for non-optimized devstack. Instead, update_assets must be
invoked each time that changes have been made.
"""

########################## Devstack settings ###################################

from openedx.stanford.cms.envs.devstack import *  # pylint: disable=wildcard-import, unused-wildcard-import

TEST_ROOT = REPO_ROOT / "test_root"

############################ STATIC FILES #############################

# Enable debug so that static assets are served by Django
DEBUG = True

# Set REQUIRE_DEBUG to false so that it behaves like production
REQUIRE_DEBUG = False

#  Serve static files at /static directly from the staticfiles directory under test root.
# Note: optimized files for testing are generated with settings from test_static_optimized
STATIC_URL = "/static/"
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
)
STATICFILES_DIRS = (
    (TEST_ROOT / "staticfiles" / "cms").abspath(),
)
