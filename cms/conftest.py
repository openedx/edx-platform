"""
Studio unit test configuration and fixtures.

This module needs to exist because the pytest.ini in the cms package stops
pytest from looking for the conftest.py module in the parent directory when
only running cms tests.
"""


import importlib
import logging
import os

import contracts
import pytest

from openedx.core.pytest_hooks import DeferPlugin

# Patch the xml libs before anything else.
from safe_lxml import defuse_xml_libs  # isort:skip
defuse_xml_libs()


def pytest_configure(config):
    """
    Do core setup operations from manage.py before collecting tests.
    """
    if config.pluginmanager.hasplugin("pytest_jsonreport") or config.pluginmanager.hasplugin("json-report"):
        config.pluginmanager.register(DeferPlugin())
    else:
        logging.info("pytest did not register json_report correctly")

    if config.getoption('help'):
        return
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


@pytest.fixture(autouse=True)
def no_webpack_loader(monkeypatch):
    """
    Monkeypatch webpack_loader to make sure that webpack assets don't need to be
    compiled before unit tests are run.
    """
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
