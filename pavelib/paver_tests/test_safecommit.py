"""
Tests for paver safecommit quality tasks
"""
from mock import patch

import pavelib.quality
from paver.easy import call_task

from .utils import PaverTestCase


class PaverSafeCommitTest(PaverTestCase):
    """
    Test run_safecommit_report with a mocked environment in order to pass in
    opts.

    """

    def setUp(self):
        super(PaverSafeCommitTest, self).setUp()
        self.reset_task_messages()

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_safecommit_count')
    def test_safecommit_violation_number_not_found(self, _mock_count, _mock_report_dir, _mock_write_metric):
        """
        run_safecommit_report encounters an error parsing the safecommit output
        log.

        """
        _mock_count.return_value = None
        with self.assertRaises(SystemExit):
            call_task('pavelib.quality.run_safecommit_report')

    @patch.object(pavelib.quality, '_write_metric')
    @patch.object(pavelib.quality, '_prepare_report_dir')
    @patch.object(pavelib.quality, '_get_safecommit_count')
    def test_safecommit_vanilla(self, _mock_count, _mock_report_dir, _mock_write_metric):
        """
        run_safecommit_report finds violations.
        """
        _mock_count.return_value = 0
        call_task('pavelib.quality.run_safecommit_report')
