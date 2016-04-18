"""
Tests for paver quality tasks
"""
import unittest
from mock import patch

import pavelib.quality
from paver.easy import BuildFailure


class TestPaverSafeLint(unittest.TestCase):
    """
    For testing run_safelint
    """

    def setUp(self):
        super(TestPaverSafeLint, self).setUp()

        # Mock the paver @needs decorator
        self._mock_paver_needs = patch.object(pavelib.quality.run_safelint, 'needs').start()
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
    def test_safelint_violation_number_not_found(self, mock_count, mock_report_dir, mock_write_metric):  # pylint: disable=unused-argument
        """
        run_safelint encounters an error parsing the safelint output log
        """
        mock_count.return_value = None
        with self.assertRaises(BuildFailure):
            pavelib.quality.run_safelint("")

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_count_from_last_line')
    def test_jshint_vanilla(self, mock_count, mock_report_dir, mock_write_metric):  # pylint: disable=unused-argument
        """
        safelint finds violations, but a limit was not set
        """
        mock_count.return_value = 1
        pavelib.quality.run_safelint("")
