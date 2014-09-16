"""
Test the about xblock
"""
import mock
from mock import patch
import pytz
import datetime
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.conf import settings

from .helpers import LoginEnrollmentTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from student.tests.factories import UserFactory, CourseEnrollmentAllowedFactory

# HTML for registration button
REG_STR = "<form id=\"class_enroll_form\" method=\"post\" data-remote=\"true\" action=\"/change_enrollment\">"
SHIB_ERROR_STR = "The currently logged-in user account does not have permission to enroll in this course."


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AboutTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    def setUp(self):
        self.course = CourseFactory.create()
        self.about = ItemFactory.create(
            category="about", parent_location=self.course.location,
            data="OOGIE BLOOGIE", display_name="overview"
        )

    def test_logged_in(self):
        self.setup_user()
        url = reverse('about_course', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)

    def test_anonymous_user(self):
        url = reverse('about_course', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)

        # Check that registration button is present
        self.assertIn(REG_STR, resp.content)

    @patch.dict(settings.FEATURES, {'ENABLE_MKTG_SITE': True})    
    def test_logged_in_marketing(self):
        self.setup_user()
        url = reverse('about_course', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        # should be redirected
        self.assertEqual(resp.status_code, 302)
        # follow this time, and check we're redirected to the course info page
        resp = self.client.get(url, follow=True)
        target_url = resp.redirect_chain[-1][0]
        info_url = reverse('info', args=[self.course.id.to_deprecated_string()])
        self.assertTrue(target_url.endswith(info_url))


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AboutTestCaseXML(LoginEnrollmentTestCase, ModuleStoreTestCase):
    # The following XML test course (which lives at common/test/data/2014)
    # is closed; we're testing that an about page still appears when
    # the course is already closed
    xml_course_id = SlashSeparatedCourseKey('edX', 'detached_pages', '2014')

    # this text appears in that course's about page
    # common/test/data/2014/about/overview.html
    xml_data = "about page 463139"

    @mock.patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_logged_in_xml(self):
        self.setup_user()
        url = reverse('about_course', args=[self.xml_course_id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.xml_data, resp.content)

    @mock.patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_anonymous_user_xml(self):
        url = reverse('about_course', args=[self.xml_course_id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.xml_data, resp.content)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AboutWithCappedEnrollmentsTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    This test case will check the About page when a course has a capped enrollment
    """
    def setUp(self):
        """
        Set up the tests
        """
        self.course = CourseFactory.create(metadata={"max_student_enrollments_allowed": 1})

        self.about = ItemFactory.create(
            category="about", parent_location=self.course.location,
            data="OOGIE BLOOGIE", display_name="overview"
        )

    def test_enrollment_cap(self):
        """
        This test will make sure that enrollment caps are enforced
        """
        self.setup_user()
        url = reverse('about_course', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<a href="#" class="register">', resp.content)

        self.enroll(self.course, verify=True)

        # create a new account since the first account is already registered for the course
        self.email = 'foo_second@test.com'
        self.password = 'bar'
        self.username = 'test_second'
        self.create_account(self.username,
                            self.email, self.password)
        self.activate_user(self.email)
        self.login(self.email, self.password)

        # Get the about page again and make sure that the page says that the course is full
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Course is full", resp.content)

        # Try to enroll as well
        result = self.enroll(self.course)
        self.assertFalse(result)

        # Check that registration button is not present
        self.assertNotIn(REG_STR, resp.content)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AboutWithInvitationOnly(ModuleStoreTestCase):
    """
    This test case will check the About page when a course is invitation only.
    """
    def setUp(self):

        self.course = CourseFactory.create(metadata={"invitation_only": True})

        self.about = ItemFactory.create(
            category="about", parent_location=self.course.location,
            display_name="overview"
        )

    def test_invitation_only(self):
        """
        Test for user not logged in, invitation only course.
        """

        url = reverse('about_course', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Enrollment in this course is by invitation only", resp.content)

        # Check that registration button is not present
        self.assertNotIn(REG_STR, resp.content)

    def test_invitation_only_but_allowed(self):
        """
        Test for user logged in and allowed to enroll in invitation only course.
        """

        # Course is invitation only, student is allowed to enroll and logged in
        user = UserFactory.create(username='allowed_student', password='test', email='allowed_student@test.com')
        CourseEnrollmentAllowedFactory(email=user.email, course_id=self.course.id)
        self.client.login(username=user.username, password='test')

        url = reverse('about_course', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Register for 999", resp.content)

        # Check that registration button is present
        self.assertIn(REG_STR, resp.content)


@patch.dict(settings.FEATURES, {'RESTRICT_ENROLL_BY_REG_METHOD': True})
@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AboutTestCaseShibCourse(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Test cases covering about page behavior for courses that use shib enrollment domain ("shib courses")
    """
    def setUp(self):
        self.course = CourseFactory.create(enrollment_domain="shib:https://idp.stanford.edu/")

        self.about = ItemFactory.create(
            category="about", parent_location=self.course.location,
            data="OOGIE BLOOGIE", display_name="overview"
        )

    def test_logged_in_shib_course(self):
        """
        For shib courses, logged in users will see the register button, but get rejected once they click there
        """
        self.setup_user()
        url = reverse('about_course', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)
        self.assertIn("Register for 999", resp.content)
        self.assertIn(SHIB_ERROR_STR, resp.content)
        self.assertIn(REG_STR, resp.content)

    def test_anonymous_user_shib_course(self):
        """
        For shib courses, anonymous users will also see the register button
        """
        url = reverse('about_course', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)
        self.assertIn("Register for 999", resp.content)
        self.assertIn(SHIB_ERROR_STR, resp.content)
        self.assertIn(REG_STR, resp.content)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AboutWithClosedEnrollment(ModuleStoreTestCase):
    """
    This test case will check the About page for a course that has enrollment start/end
    set but it is currently outside of that period.
    """
    def setUp(self):

        super(AboutWithClosedEnrollment, self).setUp()
        self.course = CourseFactory.create(metadata={"invitation_only": False})

        # Setup enrollment period to be in future
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        nextday = tomorrow + datetime.timedelta(days=1)

        self.course.enrollment_start = tomorrow
        self.course.enrollment_end = nextday
        self.course = self.update_course(self.course, self.user.id)

        self.about = ItemFactory.create(
            category="about", parent_location=self.course.location,
            display_name="overview"
        )

    def test_closed_enrollmement(self):

        url = reverse('about_course', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Enrollment is Closed", resp.content)

        # Check that registration button is not present
        self.assertNotIn(REG_STR, resp.content)
