"""
Extremely basic tests for the cert_whitelist command
"""
import pytest
from django.core.management import call_command

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.certificates.api import is_on_allowlist
from lms.djangoapps.certificates.tests.factories import CertificateAllowlistFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


def test_cert_whitelist_help(capsys):
    """
    Basic test to see if the command will parse and get args
    """
    with pytest.raises(SystemExit):
        call_command('cert_whitelist', '--help')

    out, err = capsys.readouterr()  # pylint: disable=unused-variable
    assert "COURSE_ID" in out


class CertAllowlistManagementCommandTests(ModuleStoreTestCase):
    """
    Tests for the cert_whitelist management command.
    """
    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.user2 = UserFactory()
        self.course_run = CourseFactory()
        self.course_run_key = self.course_run.id  # pylint: disable=no-member

        CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course_run_key,
            is_active=True,
            mode="verified",
        )
        CourseEnrollmentFactory(
            user=self.user2,
            course_id=self.course_run_key,
            is_active=True,
            mode="verified",
        )

    def test_allowlist_entry_created(self):
        """
        Verify an allowlist entry can be made using the management command.
        """
        call_command(
            "cert_whitelist",
            "--add",
            f"{self.user.username},{self.user2.username}",
            "-c",
            f"{self.course_run_key}")

        assert is_on_allowlist(self.user, self.course_run_key)

        assert is_on_allowlist(self.user2, self.course_run_key)

    def test_allowlist_removal(self):
        """
        Verify an allowlist entry can be removed using the management command.
        """
        CertificateAllowlistFactory.create(course_id=self.course_run_key, user=self.user)
        assert is_on_allowlist(self.user, self.course_run_key)

        call_command(
            "cert_whitelist",
            "--del",
            f"{self.user.username}",
            "-c",
            f"{self.course_run_key}")

        assert not is_on_allowlist(self.user, self.course_run_key)

    def test_bad_user_account(self):
        """
        Verify that the management command will continue processing when running into a user account problem.
        """
        call_command("cert_whitelist", "--add", f"gumby,{self.user.username}", "-c", f"{self.course_run_key}")

        assert is_on_allowlist(self.user, self.course_run_key)
