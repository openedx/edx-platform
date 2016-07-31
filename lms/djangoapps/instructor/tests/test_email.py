"""
Unit tests for email feature flag in new instructor dashboard.
Additionally tests that bulk email is always disabled for
non-Mongo backed courses, regardless of email feature flag, and
that the view is conditionally available when Course Auth is turned on.
"""

from django.core.urlresolvers import reverse
from nose.plugins.attrib import attr
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from bulk_email.models import CourseAuthorization, BulkEmailFlag
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_MIXED_MODULESTORE, SharedModuleStoreTestCase
)
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.factories import CourseFactory


@attr('shard_1')
class TestNewInstructorDashboardEmailViewMongoBacked(SharedModuleStoreTestCase):
    """
    Check for email view on the new instructor dashboard
    for Mongo-backed courses
    """
    @classmethod
    def setUpClass(cls):
        super(TestNewInstructorDashboardEmailViewMongoBacked, cls).setUpClass()
        cls.course = CourseFactory.create()

        # URL for instructor dash
        cls.url = reverse('instructor_dashboard', kwargs={'course_id': cls.course.id.to_deprecated_string()})
        # URL for email view
        cls.email_link = '<a href="" data-section="send_email">Email</a>'

    def setUp(self):
        super(TestNewInstructorDashboardEmailViewMongoBacked, self).setUp()

        # Create instructor account
        instructor = AdminFactory.create()
        self.client.login(username=instructor.username, password="test")

    def tearDown(self):
        super(TestNewInstructorDashboardEmailViewMongoBacked, self).tearDown()
        BulkEmailFlag.objects.all().delete()

    # In order for bulk email to work, we must have both the BulkEmailFlag.is_enabled()
    # set to True and for the course to be Mongo-backed.
    # The flag is enabled and the course is Mongo-backed (should work)
    def test_email_flag_true_mongo_true(self):
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)
        # Assert that instructor email is enabled for this course - since REQUIRE_COURSE_EMAIL_AUTH is False,
        # all courses should be authorized to use email.
        self.assertTrue(BulkEmailFlag.feature_enabled(self.course.id))
        # Assert that the URL for the email view is in the response
        response = self.client.get(self.url)
        self.assertIn(self.email_link, response.content)

        send_to_label = '<div class="send_to_list">Send to:</div>'
        self.assertIn(send_to_label, response.content)
        self.assertEqual(response.status_code, 200)

    # The course is Mongo-backed but the flag is disabled (should not work)
    def test_email_flag_false_mongo_true(self):
        BulkEmailFlag.objects.create(enabled=False)
        # Assert that the URL for the email view is not in the response
        response = self.client.get(self.url)
        self.assertNotIn(self.email_link, response.content)

    # Flag is enabled, but we require course auth and haven't turned it on for this course
    def test_course_not_authorized(self):
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=True)
        # Assert that instructor email is not enabled for this course
        self.assertFalse(BulkEmailFlag.feature_enabled(self.course.id))
        # Assert that the URL for the email view is not in the response
        response = self.client.get(self.url)
        self.assertNotIn(self.email_link, response.content)

    # Flag is enabled, we require course auth and turn it on for this course
    def test_course_authorized(self):
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=True)
        # Assert that instructor email is not enabled for this course
        self.assertFalse(BulkEmailFlag.feature_enabled(self.course.id))
        # Assert that the URL for the email view is not in the response
        response = self.client.get(self.url)
        self.assertNotIn(self.email_link, response.content)

        # Authorize the course to use email
        cauth = CourseAuthorization(course_id=self.course.id, email_enabled=True)
        cauth.save()

        # Assert that instructor email is enabled for this course
        self.assertTrue(BulkEmailFlag.feature_enabled(self.course.id))
        # Assert that the URL for the email view is in the response
        response = self.client.get(self.url)
        self.assertIn(self.email_link, response.content)

    # Flag is disabled, but course is authorized
    def test_course_authorized_feature_off(self):
        BulkEmailFlag.objects.create(enabled=False, require_course_email_auth=True)
        # Authorize the course to use email
        cauth = CourseAuthorization(course_id=self.course.id, email_enabled=True)
        cauth.save()

        # Assert that this course is authorized for instructor email, but the feature is not enabled
        self.assertFalse(BulkEmailFlag.feature_enabled(self.course.id))
        self.assertTrue(CourseAuthorization.instructor_email_enabled(self.course.id))
        # Assert that the URL for the email view IS NOT in the response
        response = self.client.get(self.url)
        self.assertNotIn(self.email_link, response.content)


@attr('shard_1')
class TestNewInstructorDashboardEmailViewXMLBacked(SharedModuleStoreTestCase):
    """
    Check for email view on the new instructor dashboard
    """

    MODULESTORE = TEST_DATA_MIXED_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(TestNewInstructorDashboardEmailViewXMLBacked, cls).setUpClass()
        cls.course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

        # URL for instructor dash
        cls.url = reverse('instructor_dashboard', kwargs={'course_id': cls.course_key.to_deprecated_string()})
        # URL for email view
        cls.email_link = '<a href="" data-section="send_email">Email</a>'

    def setUp(self):
        super(TestNewInstructorDashboardEmailViewXMLBacked, self).setUp()

        # Create instructor account
        instructor = AdminFactory.create()
        self.client.login(username=instructor.username, password="test")

        # URL for instructor dash
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course_key.to_deprecated_string()})
        # URL for email view
        self.email_link = '<a href="" data-section="send_email">Email</a>'

    def tearDown(self):
        super(TestNewInstructorDashboardEmailViewXMLBacked, self).tearDown()
        BulkEmailFlag.objects.all().delete()

    # The flag is enabled, and since REQUIRE_COURSE_EMAIL_AUTH is False, all courses should
    # be authorized to use email. But the course is not Mongo-backed (should not work)
    def test_email_flag_true_mongo_false(self):
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)
        response = self.client.get(self.url)
        self.assertNotIn(self.email_link, response.content)

    # The flag is disabled and the course is not Mongo-backed (should not work)
    def test_email_flag_false_mongo_false(self):
        BulkEmailFlag.objects.create(enabled=False, require_course_email_auth=False)
        response = self.client.get(self.url)
        self.assertNotIn(self.email_link, response.content)
