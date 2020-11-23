"""
Tests for Paver's Stylelint tasks.
"""


import ddt
from mock import MagicMock, patch
from paver.easy import call_task

from .utils import PaverTestCase


@ddt.ddt
class TestPaverStylelint(PaverTestCase):
    """
    Tests for Paver's Stylelint tasks.
    """
    @ddt.data(
        [0, False],
        [99, False],
        [100, True],
    )
    @ddt.unpack
    def test_run_stylelint(self, violations_limit, should_pass):
        """
        Verify that the quality task fails with Stylelint violations.
        """
        _mock_stylelint_violations = MagicMock(return_value=100)
        with patch('pavelib.quality._get_stylelint_violations', _mock_stylelint_violations):
            if should_pass:
                call_task('pavelib.quality.run_stylelint', options={"limit": violations_limit})
            else:
                with self.assertRaises(SystemExit):
                    call_task('pavelib.quality.run_stylelint', options={"limit": violations_limit})
