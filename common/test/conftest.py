"""Code run by pylint before running any tests."""

# Patch the xml libs before anything else.


from openedx.core.pytest_hooks import pytest_configure  # pylint: disable=unused-import
from safe_lxml import defuse_xml_libs

defuse_xml_libs()
