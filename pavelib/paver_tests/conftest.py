"""
Pytest fixtures for the pavelib unit tests.
"""


import os
from shutil import rmtree

import pytest

from pavelib.utils.envs import Env
from openedx.core.pytest_hooks import pytest_json_modifyreport  # pylint: disable=unused-import
from openedx.core.pytest_hooks import pytest_sessionfinish  # pylint: disable=unused-import


@pytest.fixture(autouse=True, scope='session')
def delete_quality_junit_xml():
    """
    Delete the JUnit XML results files for quality check tasks run during the
    unit tests.
    """
    yield
    if os.path.exists(Env.QUALITY_DIR):
        rmtree(Env.QUALITY_DIR, ignore_errors=True)
