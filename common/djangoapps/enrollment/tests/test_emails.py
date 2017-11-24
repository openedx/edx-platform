"""
Tests for e-mail notifications related to user enrollment.
"""
import unittest

from django.conf import settings
from django.core import mail
from django.test.utils import override_settings
from nose.plugins.attrib import attr
from rest_framework.test import APITestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from openedx.features.enterprise_support.tests.mixins.enterprise import EnterpriseServiceMockMixin
from student.tests.factories import UserFactory
from .test_views import EnrollmentTestMixin


@attr(shard=3)
@override_settings(EDX_API_KEY="i am a key")
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@override_settings(ENROLLMENT_NOTIFICATION_EMAIL="some_admins@example.com")
class EnrollmentEmailNotificationTest(EnrollmentTestMixin,
                                      ModuleStoreTestCase,
                                      APITestCase,
                                      EnterpriseServiceMockMixin):
    """
    Test e-mails sent to staff when a students enrolls to a course.
    """
    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"

    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']
    ENABLED_SIGNALS = ['course_published']

    def setUp(self):
        """ Create a course and user, then log in. Also creates a course mode."""
        # This function is a simplified version of test_views.EnrollmentTest.setUp

        super(EnrollmentEmailNotificationTest, self).setUp()

        # Pass emit_signals when creating the course so it would be cached
        # as a CourseOverview.
        self.course = CourseFactory.create(emit_signals=True)

        self.user = UserFactory.create(
            username=self.USERNAME,
            email=self.EMAIL,
            password=self.PASSWORD,
        )
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug=CourseMode.DEFAULT_MODE_SLUG,
            mode_display_name=CourseMode.DEFAULT_MODE_SLUG,
        )

    def test_email_sent_to_staff_after_enrollment(self):
        """
        Tests that an e-mail is sent on enrollment (but not on other events like unenrollment).
        """
        assert len(mail.outbox) == 0

        # Create an enrollment and verify some data
        self.assert_enrollment_status()

        assert len(mail.outbox) == 1

        msg = mail.outbox[0]
        assert msg.subject == "New student enrollment"
        assert msg.to == ["some_admins@example.com"]

        # unenroll and check that unenrollment doesn't send additional e-mails
        self.assert_enrollment_status(
            as_server=True,
            is_active=False,
        )
        assert len(mail.outbox) == 1
