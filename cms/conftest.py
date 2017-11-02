"""
Studio unit test configuration and fixtures.

This module needs to exist because the pytest.ini in the cms package stops
pytest from looking for the conftest.py module in the parent directory when
only running cms tests.
"""

from __future__ import absolute_import, unicode_literals

import importlib
import os
import contracts
import pytest
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


def pytest_configure(config):
    """
    Do core setup operations from manage.py before collecting tests.
    """
    if config.getoption('help'):
        return
    _NodeReporter.write_captured_output = write_captured_output
    enable_contracts = os.environ.get('ENABLE_CONTRACTS', False)
    if not enable_contracts:
        contracts.disable_all()
    settings_module = os.environ.get('DJANGO_SETTINGS_MODULE')
    startup_module = 'cms.startup' if settings_module.startswith('cms') else 'lms.startup'
    startup = importlib.import_module(startup_module)
    startup.run()


@pytest.fixture(autouse=True, scope='function')
def _django_clear_site_cache():
    """
    pytest-django uses this fixture to automatically clear the Site object
    cache by replacing it with a new dictionary.  edx-django-sites-extensions
    grabs the cache dictionary at startup, and uses that one for all lookups
    from then on.  Our CacheIsolationMixin class tries to clear the cache by
    grabbing the current dictionary from the site models module and clearing
    it.  Long story short: if you use this all together, neither cache
    clearing mechanism actually works.  So override this fixture to not mess
    with what has been working for us so far.
    """
    pass
