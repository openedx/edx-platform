"""
Unit tests for email feature flag in legacy instructor dashboard.
Additionally tests that bulk email is always disabled for non-Mongo
backed courses, regardless of email feature flag, and that the
view is conditionally available when Course Auth is turned on.
"""
from django.test.utils import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore import ModuleStoreEnum

from bulk_email.models import CourseAuthorization

from mock import patch


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestInstructorDashboardEmailView(ModuleStoreTestCase):
    """
    Check for email view displayed with flag
    """
    def setUp(self):
        self.course = CourseFactory.create()

        # Create instructor account
        instructor = AdminFactory.create()
        self.client.login(username=instructor.username, password="test")

        # URL for instructor dash
        self.url = reverse('instructor_dashboard_legacy', kwargs={'course_id': self.course.id.to_deprecated_string()})
        # URL for email view
        self.email_link = '<a href="#" onclick="goto(\'Email\')" class="None">Email</a>'

    def tearDown(self):
        """
        Undo all patches.
        """
        patch.stopall()

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': False})
    def test_email_flag_true(self):
        # Assert that the URL for the email view is in the response
        response = self.client.get(self.url)
        self.assertTrue(self.email_link in response.content)

        # Select the Email view of the instructor dash
        session = self.client.session
        session[u'idash_mode:{0}'.format(self.course.location.course_key.to_deprecated_string())] = 'Email'
        session.save()
        response = self.client.get(self.url)

        # Ensure we've selected the view properly and that the send_to field is present.
        selected_email_link = '<a href="#" onclick="goto(\'Email\')" class="selectedmode">Email</a>'
        self.assertTrue(selected_email_link in response.content)
        send_to_label = '<label for="id_to">Send to:</label>'
        self.assertTrue(send_to_label in response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_email_flag_unauthorized(self):
        # Assert that the URL for the email view is not in the response
        # email is enabled, but this course is not authorized to send email
        response = self.client.get(self.url)
        self.assertFalse(self.email_link in response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_email_flag_authorized(self):
        # Assert that the URL for the email view is in the response
        # email is enabled, and this course is authorized to send email

        # Assert that instructor email is not enabled for this course
        self.assertFalse(CourseAuthorization.instructor_email_enabled(self.course.id))
        response = self.client.get(self.url)
        self.assertFalse(self.email_link in response.content)

        # Authorize the course to use email
        cauth = CourseAuthorization(course_id=self.course.id, email_enabled=True)
        cauth.save()

        # Assert that instructor email is enabled for this course
        self.assertTrue(CourseAuthorization.instructor_email_enabled(self.course.id))
        response = self.client.get(self.url)
        self.assertTrue(self.email_link in response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': False})
    def test_email_flag_false(self):
        # Assert that the URL for the email view is not in the response
        response = self.client.get(self.url)
        self.assertFalse(self.email_link in response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True})
    def test_email_flag_true_xml_store(self):
        # If the enable email setting is enabled, but this is an XML backed course,
        # the email view shouldn't be available on the instructor dashboard.

        # The course factory uses a MongoModuleStore backing, so patch the
        # `get_modulestore_type` method to pretend to be XML-backed.
        # This is OK; we're simply testing that the `is_mongo_modulestore_type` flag
        # in `instructor/views/legacy.py` is doing the correct thing.

        with patch('xmodule.modulestore.mongo.base.MongoModuleStore.get_modulestore_type') as mock_modulestore:
            mock_modulestore.return_value = ModuleStoreEnum.Type.xml

            # Assert that the URL for the email view is not in the response
            response = self.client.get(self.url)
            self.assertFalse(self.email_link in response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True})
    def test_send_mail_unauthorized(self):
        """ Test 'Send email' action returns an error if course is not authorized to send email. """

        response = self.client.post(
            self.url, {
                'action': 'Send email',
                'to_option': 'all',
                'subject': "Welcome to the course!",
                'message': "Lets start with an introduction!"
            }
        )
        self.assertContains(response, "Email is not enabled for this course.")

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True})
    def test_send_mail_authorized(self):
        """ Test 'Send email' action when course is authorized to send email. """

        course_authorization = CourseAuthorization(course_id=self.course.id, email_enabled=True)
        course_authorization.save()

        session = self.client.session
        session[u'idash_mode:{0}'.format(self.course.location.course_key.to_deprecated_string())] = 'Email'
        session.save()

        response = self.client.post(
            self.url, {
                'action': 'Send email',
                'to_option': 'all',
                'subject': 'Welcome to the course!',
                'message': 'Lets start with an introduction!',
            }
        )
        self.assertContains(response, "Your email was successfully queued for sending.")
