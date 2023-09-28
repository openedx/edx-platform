"""
Tests for Paver's Stylelint tasks.
"""


import unittest
from unittest.mock import patch

import pytest
from paver.easy import BuildFailure, call_task

import pavelib.quality


class TestPaverESLint(unittest.TestCase):
    """
    For testing run_eslint
    """

    def setUp(self):
        super().setUp()

        # Mock the paver @needs decorator
        self._mock_paver_needs = patch.object(pavelib.quality.run_eslint, 'needs').start()
        self._mock_paver_needs.return_value = 0

        # Mock shell commands
        patcher = patch('pavelib.quality.sh')
        self._mock_paver_sh = patcher.start()

        # Cleanup mocks
        self.addCleanup(patcher.stop)
        self.addCleanup(self._mock_paver_needs.stop)

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_count_from_last_line')
    def test_eslint_violation_number_not_found(self, mock_count, mock_report_dir, mock_write_metric):  # pylint: disable=unused-argument
        """
        run_eslint encounters an error parsing the eslint output log
        """
        mock_count.return_value = None
        with pytest.raises(BuildFailure):
            call_task('pavelib.quality.run_eslint', args=[''])

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_count_from_last_line')
    def test_eslint_vanilla(self, mock_count, mock_report_dir, mock_write_metric):  # pylint: disable=unused-argument
        """
        eslint finds violations, but a limit was not set
        """
        mock_count.return_value = 1
        pavelib.quality.run_eslint("")
