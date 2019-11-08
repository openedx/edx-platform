"""Code run by pylint before running any tests."""

# Patch the xml libs before anything else.
from __future__ import absolute_import

import openedx.core.pytest_hooks as pytest_hooks
from safe_lxml import defuse_xml_libs

defuse_xml_libs()


class DeferPlugin(object):
    """Simple plugin to defer pytest-xdist hook functions."""

    def pytest_json_modifyreport(self, json_report):
        """standard xdist hook function.
        """
        return pytest_hooks.pytest_json_modifyreport(json_report)


    def pytest_sessionfinish(self, session):
        return pytest_sessionfinish(session)


def pytest_configure(config):
    if config.pluginmanager.hasplugin("json-report"):
        config.pluginmanager.register(DeferPlugin())
