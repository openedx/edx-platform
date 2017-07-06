"""
Tests for paver safelint quality tasks
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
    @patch.object(pavelib.quality, '_get_safelint_counts')
    def test_safelint_violation_number_not_found(self, _mock_counts, _mock_report_dir, _mock_write_metric):
        """
        run_safelint encounters an error parsing the safelint output log
        """
        _mock_counts.return_value = {}
        with self.assertRaises(SystemExit):
            call_task('pavelib.quality.run_safelint')

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_safelint_counts')
    def test_safelint_vanilla(self, _mock_counts, _mock_report_dir, _mock_write_metric):
        """
        run_safelint finds violations, but a limit was not set
        """
        _mock_counts.return_value = {'total': 0}
        call_task('pavelib.quality.run_safelint')

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_safelint_counts')
    def test_safelint_invalid_thresholds_option(self, _mock_counts, _mock_report_dir, _mock_write_metric):
        """
        run_safelint fails when thresholds option is poorly formatted
        """
        _mock_counts.return_value = {'total': 0}
        with self.assertRaises(SystemExit):
            call_task('pavelib.quality.run_safelint', options={"thresholds": "invalid"})

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_safelint_counts')
    def test_safelint_invalid_thresholds_option_key(self, _mock_counts, _mock_report_dir, _mock_write_metric):
        """
        run_safelint fails when thresholds option is poorly formatted
        """
        _mock_counts.return_value = {'total': 0}
        with self.assertRaises(SystemExit):
            call_task('pavelib.quality.run_safelint', options={"thresholds": '{"invalid": 3}'})

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_safelint_counts')
    def test_safelint_too_many_violations(self, _mock_counts, _mock_report_dir, _mock_write_metric):
        """
        run_safelint finds more violations than are allowed
        """
        _mock_counts.return_value = {'total': 4}
        with self.assertRaises(SystemExit):
            call_task('pavelib.quality.run_safelint', options={"thresholds": '{"total": 3}'})

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_safelint_counts')
    def test_safelint_under_limit(self, _mock_counts, _mock_report_dir, _mock_write_metric):
        """
        run_safelint finds fewer violations than are allowed
        """
        _mock_counts.return_value = {'total': 4}
        # No System Exit is expected
        call_task('pavelib.quality.run_safelint', options={"thresholds": '{"total": 5}'})

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_safelint_counts')
    def test_safelint_rule_violation_number_not_found(self, _mock_counts, _mock_report_dir, _mock_write_metric):
        """
        run_safelint encounters an error parsing the safelint output log for a
        given rule threshold that was set.
        """
        _mock_counts.return_value = {'total': 4}
        with self.assertRaises(SystemExit):
            call_task('pavelib.quality.run_safelint', options={"thresholds": '{"rules": {"javascript-escape": 3}}'})

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_safelint_counts')
    def test_safelint_too_many_rule_violations(self, _mock_counts, _mock_report_dir, _mock_write_metric):
        """
        run_safelint finds more rule violations than are allowed
        """
        _mock_counts.return_value = {'total': 4, 'rules': {'javascript-escape': 4}}
        with self.assertRaises(SystemExit):
            call_task('pavelib.quality.run_safelint', options={"thresholds": '{"rules": {"javascript-escape": 3}}'})

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_safelint_counts')
    def test_safelint_under_rule_limit(self, _mock_counts, _mock_report_dir, _mock_write_metric):
        """
        run_safelint finds fewer rule violations than are allowed
        """
        _mock_counts.return_value = {'total': 4, 'rules': {'javascript-escape': 4}}
        # No System Exit is expected
        call_task('pavelib.quality.run_safelint', options={"thresholds": '{"rules": {"javascript-escape": 5}}'})
