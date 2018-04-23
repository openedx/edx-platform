"""
Extremely basic tests for the gen_cert_report command
"""
import pytest

from nose.plugins.attrib import attr
from django.core.management import call_command


@attr(shard=4)
def test_cert_report_help(capsys):
    """
    Basic test to see if the command will parse and get args
    """
    with pytest.raises(SystemExit):
        call_command('gen_cert_report', '--help')

    out, err = capsys.readouterr()  # pylint: disable=unused-variable
    assert "COURSE_ID" in out
