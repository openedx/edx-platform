"""Code run by pylint before running any tests."""

# Patch the xml libs before anything else.


import pytest

from safe_lxml import defuse_xml_libs

# This import is needed for pytest plugin configuration, so please avoid deleting this during refactoring
from openedx.core.pytest_hooks import pytest_configure  # pylint: disable=unused-import

defuse_xml_libs()


@pytest.fixture(autouse=True)
def no_webpack_loader(monkeypatch):  # lint-amnesty, pylint: disable=missing-function-docstring
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
