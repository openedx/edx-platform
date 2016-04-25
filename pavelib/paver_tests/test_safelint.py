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
    def test_safelint_violation_number_not_found(self, _mock_count, _mock_report_dir, _mock_write_metric):
        """
        run_safelint encounters an error parsing the safelint output log
        """
        _mock_count.return_value = None
        with self.assertRaises(BuildFailure):
            pavelib.quality.run_safelint("")

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_count_from_last_line')
    def test_safelint_vanilla(self, _mock_count, _mock_report_dir, _mock_write_metric):
        """
        safelint finds violations, but a limit was not set
        """
        _mock_count.return_value = 1
        pavelib.quality.run_safelint("")
