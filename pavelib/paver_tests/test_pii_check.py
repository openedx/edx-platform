"""
Tests for Paver's PII checker task.
"""
from __future__ import absolute_import

import io

import six
from mock import patch
from paver.easy import call_task

import pavelib.quality
from pavelib.utils.envs import Env


@patch.object(pavelib.quality.run_pii_check, 'needs')
@patch('pavelib.quality.sh')
def test_pii_check_report_dir_override(mock_paver_sh, mock_needs, tmpdir):
    """
    run_pii_check succeeds with proper report dir
    """
    # Make the expected stdout files.
    report_dir = tmpdir.mkdir('pii_report')
    cms_stdout_report = report_dir.join('pii_check_cms.report')
    cms_stdout_report.write('Coverage found 33 uncovered models:\n')
    lms_stdout_report = report_dir.join('pii_check_lms.report')
    lms_stdout_report.write('Coverage found 66 uncovered models:\n')

    mock_needs.return_value = 0
    call_task('pavelib.quality.run_pii_check', options={"report_dir": six.text_type(report_dir)})
    mock_calls = [six.text_type(call) for call in mock_paver_sh.mock_calls]
    assert len(mock_calls) == 2
    assert any(['lms.envs.test' in call for call in mock_calls])
    assert any(['cms.envs.test' in call for call in mock_calls])
    assert all([six.text_type(report_dir) in call for call in mock_calls])
    metrics_file = Env.METRICS_DIR / 'pii'
    assert io.open(metrics_file, 'r').read() == '66'
