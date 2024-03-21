"""
Tests for pavelib/i18n.py.
"""

import os
from unittest.mock import patch

from paver.easy import call_task

import pavelib.i18n
from pavelib.paver_tests.utils import PaverTestCase


class TestI18nDummy(PaverTestCase):
    """
    Test the Paver i18n_dummy task.
    """
    def setUp(self):
        super().setUp()

        # Mock the paver @needs decorator for i18n_extract
        self._mock_paver_needs = patch.object(pavelib.i18n.i18n_extract, 'needs').start()
        self._mock_paver_needs.return_value = 0

        # Cleanup mocks
        self.addCleanup(self._mock_paver_needs.stop)

    def test_i18n_dummy(self):
        """
        Test the "i18n_dummy" task.
        """
        self.reset_task_messages()
        os.environ['NO_PREREQ_INSTALL'] = "true"
        call_task('pavelib.i18n.i18n_dummy')
        assert self.task_messages == ['i18n_tool extract', 'i18n_tool dummy', 'i18n_tool generate']
