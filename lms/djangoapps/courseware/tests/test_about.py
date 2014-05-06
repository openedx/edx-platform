"""
Test the about xblock
"""
import mock
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from .helpers import LoginEnrollmentTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.locations import SlashSeparatedCourseKey


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
