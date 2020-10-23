"""
Default unit test configuration and fixtures.
"""

from unittest import TestCase

import pytest

from adg_pipelines.skip_tests import TEST_SKIP_LIST

# Import hooks and fixture overrides from the cms package to
# avoid duplicating the implementation

from cms.conftest import _django_clear_site_cache, pytest_configure  # pylint: disable=unused-import


# When using self.assertEquals, diffs are truncated. We don't want that, always
# show the whole diff.
TestCase.maxDiff = None


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


def pytest_collection_modifyitems(items):
    """
    Add skip annotation to a list of tests, so that they do not run.

    Args:
        items (list): A list of tests to skip

    Returns:
        None
    """
    items_to_skip = [item for item in items if item.nodeid in TEST_SKIP_LIST]

    if not items_to_skip:
        return

    print("Explicitly skipping following tests")
    skip_listed = pytest.mark.skip(reason="included in --skiplist")

    for item in items_to_skip:
        item.add_marker(skip_listed)
        print(item.nodeid)
