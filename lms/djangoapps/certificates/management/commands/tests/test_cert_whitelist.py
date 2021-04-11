"""
Extremely basic tests for the cert_whitelist command
"""


import pytest
from django.core.management import call_command


def test_cert_whitelist_help(capsys):
    """
    Basic test to see if the command will parse and get args
    """
    with pytest.raises(SystemExit):
        call_command('cert_whitelist', '--help')

    out, err = capsys.readouterr()  # pylint: disable=unused-variable
    assert "COURSE_ID" in out
