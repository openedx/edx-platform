"""
Default unit test configuration and fixtures.
"""

from __future__ import absolute_import, unicode_literals

# Import hooks and fixture overrides from the cms package to
# avoid duplicating the implementation

from cms.conftest import _django_clear_site_cache, pytest_configure  # pylint: disable=unused-import
