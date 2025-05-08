"""  # lint-amnesty, pylint: disable=django-not-configured
Default unit test configuration and fixtures.
"""

from unittest import TestCase

import pytest

# Import hooks and fixture overrides from the cms package to
# avoid duplicating the implementation

from cms.conftest import _django_clear_site_cache, pytest_configure  # pylint: disable=unused-import

from webpack_loader.templatetags import webpack_loader

# When using self.assertEquals, diffs are truncated. We don't want that, always
# show the whole diff.
TestCase.maxDiff = None


@pytest.fixture(autouse=True)
def patch_render_bundle(monkeypatch):
   """Monkey Patch the template tag to prevent errors due to missing bundles"""
   monkeypatch.setattr(
       webpack_loader,
       "render_bundle",
       lambda bundle_name, extension=None, config="DEFAULT", attrs="": ""
   )