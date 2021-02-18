"""
Tests for the cert_allowlist command
"""

import mock
import pytest
from django.core.management import CommandError, call_command
from edx_toggles.toggles.testutils import override_waffle_flag
from waffle.testutils import override_switch
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.certificates.generation_handler import CERTIFICATES_USE_ALLOWLIST
from lms.djangoapps.certificates.tests.factories import CertificateWhitelistFactory
from lms.djangoapps.certificates.tests.test_generation_handler import (
    AUTO_GENERATION_SWITCH_NAME,
    ID_VERIFIED_METHOD
)


@override_switch(AUTO_GENERATION_SWITCH_NAME, active=True)
@override_waffle_flag(CERTIFICATES_USE_ALLOWLIST, active=True)
@mock.patch(ID_VERIFIED_METHOD, mock.Mock(return_value=True))
class CertAllowlistGenerationTests(ModuleStoreTestCase):
    """
    Tests for the cert_allowlist_generation management command
    """

    def setUp(self):
        super().setUp()

        # Create users, a course run, and enrollments
        self.user = UserFactory()
        self.course_run = CourseFactory()
        self.course_run_key = self.course_run.id  # pylint: disable=no-member
        self.enrollment = CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course_run_key,
            is_active=True,
            mode="verified",
        )

        self.user2 = UserFactory()
        self.enrollment2 = CourseEnrollmentFactory(
            user=self.user2,
            course_id=self.course_run_key,
            is_active=True,
            mode="verified",
        )

        # Whitelist users
        CertificateWhitelistFactory.create(course_id=self.course_run_key, user=self.user)
        CertificateWhitelistFactory.create(course_id=self.course_run_key, user=self.user2)

    def test_command_with_missing_param(self):
        """
        Verify command with a missing param
        """
        with pytest.raises(CommandError, match="You must specify a course-key"):
            call_command("cert_allowlist_generation", "--u", self.user.username)

    def test_command_with_invalid_key(self):
        """
        Verify command with an invalid course run key
        """
        with pytest.raises(CommandError, match="You must specify a valid course-key"):
            call_command("cert_allowlist_generation", "--u", self.user.username, "--c", "blah")

    def test_successful_generation(self):
        """
        Test generation for 1 user
        """
        call_command("cert_allowlist_generation", "--u", self.user.id, "--c", self.course_run_key)

    def test_successful_generation_multiple_users(self):
        """
        Test generation for multiple user
        """
        call_command("cert_allowlist_generation",
                     "--u",
                     self.user.id,
                     self.user2.id,
                     "999999",  # non-existant userid
                     "--c",
                     self.course_run_key)
