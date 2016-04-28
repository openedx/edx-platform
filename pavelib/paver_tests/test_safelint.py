"""
Tests for paver quality tasks
"""
from mock import patch

import pavelib.quality
from paver.easy import call_task

from .utils import PaverTestCase


class PaverSafeLintTest(PaverTestCase):
    """
    Test run_safelint with a mocked environment in order to pass in opts
    """

    def setUp(self):
        super(PaverSafeLintTest, self).setUp()
        self.reset_task_messages()

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_count_from_last_line')
    def test_safelint_violation_number_not_found(self, _mock_count, _mock_report_dir, _mock_write_metric):
        """
        run_safelint encounters an error parsing the safelint output log
        """
        _mock_count.return_value = None
        with self.assertRaises(SystemExit):
            call_task('pavelib.quality.run_safelint')

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_count_from_last_line')
    def test_safelint_vanilla(self, _mock_count, _mock_report_dir, _mock_write_metric):
        """
        run_safelint finds violations, but a limit was not set
        """
        _mock_count.return_value = 1
        call_task('pavelib.quality.run_safelint')

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_count_from_last_line')
    def test_safelint_too_many_violations(self, _mock_count, _mock_report_dir, _mock_write_metric):
        """
        run_safelint finds more violations than are allowed
        """
        _mock_count.return_value = 4
        with self.assertRaises(SystemExit):
            call_task('pavelib.quality.run_safelint', options={"limit": "3"})

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_count_from_last_line')
    def test_safelint_under_limit(self, _mock_count, _mock_report_dir, _mock_write_metric):
        """
        run_safelint finds fewer violations than are allowed
        """
        _mock_count.return_value = 4
        # No System Exit is expected
        call_task('pavelib.quality.run_safelint', options={"limit": "5"})
