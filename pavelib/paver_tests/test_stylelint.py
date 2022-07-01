"""
Tests for Paver's Stylelint tasks.
"""

from unittest.mock import MagicMock, patch

import pytest
import ddt
from paver.easy import call_task

from .utils import PaverTestCase


@ddt.ddt
class TestPaverStylelint(PaverTestCase):
    """
    Tests for Paver's Stylelint tasks.
    """
    @ddt.data(
        [False],
        [True],
    )
    @ddt.unpack
    def test_run_stylelint(self, should_pass):
        """
        Verify that the quality task fails with Stylelint violations.
        """
        if should_pass:
            _mock_stylelint_violations = MagicMock(return_value=0)
            with patch('pavelib.quality._get_stylelint_violations', _mock_stylelint_violations):
                call_task('pavelib.quality.run_stylelint')
        else:
            _mock_stylelint_violations = MagicMock(return_value=100)
            with patch('pavelib.quality._get_stylelint_violations', _mock_stylelint_violations):
                with pytest.raises(SystemExit):
                    call_task('pavelib.quality.run_stylelint')
