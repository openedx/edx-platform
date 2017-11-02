"""
common/lib unit test configuration.
"""

from django.conf import settings
from _pytest.junitxml import _NodeReporter, bin_xml_escape, Junit


def write_captured_output(self, report):
    """
    Replacement for _NodeReporter.write_captured_output() in the junitxml
    pytest plugin.  Only outputs the captured stderr and stdout streams
    for failing tests, which dramatically reduces the size of the
    generated XML file.

    A cleaner fix has been proposed at https://github.com/pytest-dev/pytest/issues/2889
    """
    failed = any([node for node in self.nodes if node.__class__.__name__ != 'py._xmlgen.skipped'])
    if not failed:
        return
    for capname in ('out', 'err'):
        content = getattr(report, 'capstd' + capname)
        if content:
            tag = getattr(Junit, 'system-' + capname)
            self.append(tag(bin_xml_escape(content)))


def pytest_configure():
    """
    Use Django's default settings for tests in common/lib.
    """
    settings.configure()
    _NodeReporter.write_captured_output = write_captured_output
