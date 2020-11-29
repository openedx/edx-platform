"""
Unit test for environment utilities
"""

import os

from openedx.adg.lms.utils import env_utils as utils


def test_is_testing_environment(monkeypatch):
    """
    Test if the environment is set to test or not
    """

    monkeypatch.setitem(os.environ, 'DJANGO_SETTINGS_MODULE', 'lms.envs.test')
    assert utils.is_testing_environment()

    monkeypatch.setitem(os.environ, 'DJANGO_SETTINGS_MODULE', 'cms.envs.test')
    assert utils.is_testing_environment()

    monkeypatch.setitem(os.environ, 'DJANGO_SETTINGS_MODULE', 'something_other_than_test')
    assert not utils.is_testing_environment()
