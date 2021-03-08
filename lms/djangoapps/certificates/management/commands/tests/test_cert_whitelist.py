"""
Extremely basic tests for the cert_whitelist command
"""
import ddt
import pytest
from django.core.management import call_command, CommandError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


def test_cert_whitelist_help(capsys):
    """
    Basic test to see if the command will parse and get args
    """
    with pytest.raises(SystemExit):
        call_command('cert_whitelist', '--help')

    out, err = capsys.readouterr()  # pylint: disable=unused-variable
    assert "COURSE_ID" in out


@ddt.ddt
class CertWhitelistGenerationTests(ModuleStoreTestCase):
    """
    Tests for the cert_whitelist management command.
    """
    @ddt.data(
        'jeo',
        'jeo@edx.org',
        'robo_user, jenny, tom, jerry'
    )
    def test_user_not_found(self, user_identifier):
        """
        Basic test to see if the command will raise user not found error.
        """
        error_identifier = user_identifier.split(',')[0].strip()
        with pytest.raises(CommandError, match=f"User {error_identifier} does not exist"):
            call_command('cert_whitelist', '--add', user_identifier, '-c', 'MITx/6.002x/2012_Fall')
