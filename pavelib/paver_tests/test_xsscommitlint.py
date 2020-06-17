"""
Tests for paver xsscommitlint quality tasks
"""


from mock import patch
from paver.easy import call_task

import pavelib.quality

from .utils import PaverTestCase


class PaverXSSCommitLintTest(PaverTestCase):
    """
    Test run_xsscommitlint with a mocked environment in order to pass in
    opts.

    """

    def setUp(self):
        super().setUp()
        self.reset_task_messages()

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_xsscommitlint_count')
    def test_xsscommitlint_violation_number_not_found(self, _mock_count, _mock_report_dir, _mock_write_metric):
        """
        run_xsscommitlint encounters an error parsing the xsscommitlint output
        log.

        """
        _mock_count.return_value = None
        with self.assertRaises(SystemExit):
            call_task('pavelib.quality.run_xsscommitlint')

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_xsscommitlint_count')
    def test_xsscommitlint_vanilla(self, _mock_count, _mock_report_dir, _mock_write_metric):
        """
        run_xsscommitlint finds violations.
        """
        _mock_count.return_value = 0
        call_task('pavelib.quality.run_xsscommitlint')
