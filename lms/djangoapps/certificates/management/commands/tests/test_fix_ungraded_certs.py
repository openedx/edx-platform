"""
Extremely basic tests for the fix_ungraded_certs command
"""


import pytest
from django.core.management import call_command


def test_fix_ungraded_certs_help(capsys):
    """
    Basic test to see if the command will parse and get args
    """
    with pytest.raises(SystemExit):
        call_command('fix_ungraded_certs', '--help')

    out, err = capsys.readouterr()  # pylint: disable=unused-variable
    assert "COURSE_ID" in out
