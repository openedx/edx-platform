"""
Default unit test configuration and fixtures.
"""
from __future__ import absolute_import, unicode_literals
import pytest

# Imports an autouse fixture for loading Python test data.
from common.test.python.utils import load_python_test_data  # pylint: disable=unused-import

# Import hooks and fixture overrides from the cms package to
# avoid duplicating the implementation
from cms.conftest import _django_clear_site_cache, pytest_configure  # pylint: disable=unused-import


@pytest.fixture(autouse=True)
def no_webpack_loader(monkeypatch):
    monkeypatch.setattr(
        "webpack_loader.templatetags.webpack_loader.render_bundle",
        lambda entry, extension=None, config='DEFAULT', attrs='': ''
    )
    monkeypatch.setattr(
        "webpack_loader.utils.get_as_tags",
        lambda entry, extension=None, config='DEFAULT', attrs='': []
    )
    monkeypatch.setattr(
        "webpack_loader.utils.get_files",
        lambda entry, extension=None, config='DEFAULT', attrs='': []
    )
