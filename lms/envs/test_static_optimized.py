"""
Settings used when generating static assets for use in tests.

Bok Choy uses two different settings files:
1. test_static_optimized is used when invoking collectstatic
2. bok_choy is used when running CMS and LMS

Note: it isn't possible to have a single settings file, because Django doesn't
support both generating static assets to a directory and also serving static
from the same directory.

"""

# TODO: update the Bok Choy tests to run with optimized static assets (as is done in Studio)

from .bok_choy import *  # pylint: disable=wildcard-import, unused-wildcard-import
