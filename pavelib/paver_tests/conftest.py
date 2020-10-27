"""
Pytest fixtures for the pavelib unit tests.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
from shutil import rmtree

import pytest

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
