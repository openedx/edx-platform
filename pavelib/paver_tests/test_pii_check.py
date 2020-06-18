"""
Tests for Paver's PII checker task.
"""

import shutil
import tempfile
import unittest

from mock import patch
from path import Path as path
from paver.easy import call_task, BuildFailure

import pavelib.quality
from pavelib.utils.envs import Env


class TestPaverPIICheck(unittest.TestCase):
    """
    For testing the paver run_pii_check task
    """
    def setUp(self):
        super().setUp()
        self.report_dir = path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.report_dir)

    @patch.object(pavelib.quality.run_pii_check, 'needs')
    @patch('pavelib.quality.sh')
    def test_pii_check_report_dir_override(self, mock_paver_sh, mock_needs):
        """
        run_pii_check succeeds with proper report dir
        """
        # Make the expected stdout files.
        cms_stdout_report = self.report_dir / 'pii_check_cms.report'
        cms_stdout_report.write_lines(['Coverage found 33 uncovered models:\n'])
        lms_stdout_report = self.report_dir / 'pii_check_lms.report'
        lms_stdout_report.write_lines(['Coverage found 66 uncovered models:\n'])

        mock_needs.return_value = 0
        call_task('pavelib.quality.run_pii_check', options={"report_dir": str(self.report_dir)})
        mock_calls = [str(call) for call in mock_paver_sh.mock_calls]
        assert len(mock_calls) == 2
        assert any(['lms.envs.test' in call for call in mock_calls])
        assert any(['cms.envs.test' in call for call in mock_calls])
        assert all([str(self.report_dir) in call for call in mock_calls])
        metrics_file = Env.METRICS_DIR / 'pii'
        assert open(metrics_file, 'r').read() == 'Number of PII Annotation violations: 66\n'

    @patch.object(pavelib.quality.run_pii_check, 'needs')
    @patch('pavelib.quality.sh')
    def test_pii_check_failed(self, mock_paver_sh, mock_needs):
        """
        run_pii_check fails due to crossing the threshold.
        """
        # Make the expected stdout files.
        cms_stdout_report = self.report_dir / 'pii_check_cms.report'
        cms_stdout_report.write_lines(['Coverage found 33 uncovered models:\n'])
        lms_stdout_report = self.report_dir / 'pii_check_lms.report'
        lms_stdout_report.write_lines([
            'Coverage found 66 uncovered models:',
            'Coverage threshold not met! Needed 100.0, actually 95.0!',
        ])

        mock_needs.return_value = 0
        with self.assertRaises(SystemExit):
            call_task('pavelib.quality.run_pii_check', options={"report_dir": str(self.report_dir)})
            self.assertRaises(BuildFailure)
        mock_calls = [str(call) for call in mock_paver_sh.mock_calls]
        assert len(mock_calls) == 2
        assert any(['lms.envs.test' in call for call in mock_calls])
        assert any(['cms.envs.test' in call for call in mock_calls])
        assert all([str(self.report_dir) in call for call in mock_calls])
        metrics_file = Env.METRICS_DIR / 'pii'
        assert open(metrics_file, 'r').read() == 'Number of PII Annotation violations: 66\n'
