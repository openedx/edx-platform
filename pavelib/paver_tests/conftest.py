"""
Pytest fixtures for the pavelib unit tests.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
from shutil import rmtree

import pytest

from pavelib.utils.envs import Env
import openedx.core.tests.pytest_hooks.pytest_json_modifyreport as custom_hook # pylint: disable=unused-import


@pytest.fixture(autouse=True, scope='session')
def delete_quality_junit_xml():
    """
    Delete the JUnit XML results files for quality check tasks run during the
    unit tests.
    """
    yield
    if os.path.exists(Env.QUALITY_DIR):
        rmtree(Env.QUALITY_DIR, ignore_errors=True)


class DeferPlugin:
    """Simple plugin to defer pytest-xdist hook functions."""

    def pytest_json_modifyreport(self, json_report):
        """standard xdist hook function.
        """
        return custom_hook(json_report)


def pytest_configure(config):
    if config.pluginmanager.hasplugin("json-report"):
        config.pluginmanager.register(DeferPlugin())