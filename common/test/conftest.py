"""Code run by pylint before running any tests."""

# Patch the xml libs before anything else.
from __future__ import absolute_import

from openedx.core.tests.pytest_hooks import pytest_json_modifyreport

from safe_lxml import defuse_xml_libs

defuse_xml_libs()
