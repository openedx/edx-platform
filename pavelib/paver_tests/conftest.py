"""
Pytest fixtures for the pavelib unit tests.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
from shutil import rmtree

import pytest
from setproctitle import getproctitle, setproctitle

from pavelib.utils.envs import Env


@pytest.fixture(autouse=True, scope='session')
def delete_quality_junit_xml():
    """
    Delete the JUnit XML results files for quality check tasks run during the
    unit tests.
    """
    yield
    if os.path.exists(Env.QUALITY_DIR):
        rmtree(Env.QUALITY_DIR, ignore_errors=True)


def pytest_configure(config):
    """
    Rename the process for pytest-xdist workers for easier identification.
    """
    if hasattr(config, 'workerinput'):
        # Set the process name for pytest-xdist workers to something
        # recognizable, like "py_xdist_gw0", for the benefit of tools like
        # New Relic Infrastructure and top
        old_name = getproctitle()
        new_name = 'py_xdist_{}'.format(config.workerinput['workerid'])
        setproctitle(old_name.replace('python', new_name, 1))
