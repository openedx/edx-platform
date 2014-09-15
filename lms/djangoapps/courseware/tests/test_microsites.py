"""
Tests related to the Microsites feature
"""
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from helpers import LoginEnrollmentTestCase
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE

MICROSITE_TEST_HOSTNAME = 'testmicrosite.testserver'


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestMicrosites(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    This is testing of the Microsite feature
    """

    STUDENT_INFO = [('view@test.com', 'foo'), ('view2@test.com', 'foo')]

    def setUp(self):
        # use a different hostname to test Microsites since they are
        # triggered on subdomain mappings
        #
        # NOTE: The Microsite Configuration is in lms/envs/test.py. The content for the Test Microsite is in
        # test_microsites/test_microsite.
        #
        # IMPORTANT: For these tests to work, this domain must be defined via
        # DNS configuration (either local or published)

        self.course = CourseFactory.create(display_name='Robot_Super_Course', org='TestMicrositeX')
        self.chapter0 = ItemFactory.create(parent_location=self.course.location,
                                           display_name='Overview')
        self.chapter9 = ItemFactory.create(parent_location=self.course.location,
                                           display_name='factory_chapter')
        self.section0 = ItemFactory.create(parent_location=self.chapter0.location,
                                           display_name='Welcome')
        self.section9 = ItemFactory.create(parent_location=self.chapter9.location,
                                           display_name='factory_section')

        self.course_outside_microsite = CourseFactory.create(display_name='Robot_Course_Outside_Microsite', org='FooX')

    def setup_users(self):
        # Create student accounts and activate them.
        for i in range(len(self.STUDENT_INFO)):
            email, password = self.STUDENT_INFO[i]
            username = 'u{0}'.format(i)
            self.create_account(username, email, password)
            self.activate_user(email)

    @override_settings(SITE_NAME=MICROSITE_TEST_HOSTNAME)
    def test_microsite_anonymous_homepage_content(self):
        """
        Verify that the homepage, when accessed via a Microsite domain, returns
        HTML that reflects the Microsite branding elements
        """

        resp = self.client.get('/', HTTP_HOST=MICROSITE_TEST_HOSTNAME)
        self.assertEqual(resp.status_code, 200)

        # assert various branding definitions on this Microsite
        # as per the configuration and Microsite overrides

        self.assertContains(resp, 'This is a Test Microsite Overlay')   # Overlay test message
        self.assertContains(resp, 'test_microsite/images/header-logo.png')  # logo swap
        self.assertContains(resp, 'test_microsite/css/test_microsite')  # css override
        self.assertContains(resp, 'Test Microsite')   # page title

        # assert that test course display name is visible
        self.assertContains(resp, 'Robot_Super_Course')

        # assert that test course that is outside microsite is not visible
        self.assertNotContains(resp, 'Robot_Course_Outside_Microsite')

        # assert that footer template has been properly overriden on homepage
        self.assertContains(resp, 'This is a Test Microsite footer')

        # assert that the edX partners section is not in the HTML
        self.assertNotContains(resp, '<section class="university-partners university-partners2x6">')

        # assert that the edX partners tag line is not in the HTML
        self.assertNotContains(resp, 'Explore free courses from')

    def test_not_microsite_anonymous_homepage_content(self):
        """
        Make sure we see the right content on the homepage if we are not in a microsite
        """

        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

        # assert various branding definitions on this Microsite ARE NOT VISIBLE

        self.assertNotContains(resp, 'This is a Test Microsite Overlay')   # Overlay test message
        self.assertNotContains(resp, 'test_microsite/images/header-logo.png')  # logo swap
        self.assertNotContains(resp, 'test_microsite/css/test_microsite')  # css override
        self.assertNotContains(resp, '<title>Test Microsite</title>')   # page title

        # assert that test course display name IS NOT VISIBLE, since that is a Microsite only course
        self.assertNotContains(resp, 'Robot_Super_Course')

        # assert that test course that is outside microsite IS VISIBLE
        self.assertContains(resp, 'Robot_Course_Outside_Microsite')

        # assert that footer template has been properly overriden on homepage
        self.assertNotContains(resp, 'This is a Test Microsite footer')

    def test_no_redirect_on_homepage_when_no_enrollments(self):
        """
        Verify that a user going to homepage will not redirect if he/she has no course enrollments
        """
        self.setup_users()

        email, password = self.STUDENT_INFO[0]
        self.login(email, password)
        resp = self.client.get(reverse('root'), HTTP_HOST=MICROSITE_TEST_HOSTNAME)
        self.assertEquals(resp.status_code, 200)

    def test_redirect_on_homepage_when_has_enrollments(self):
        """
        Verify that a user going to homepage will redirect to dashboard if he/she has
        a course enrollment
        """
        self.setup_users()

        email, password = self.STUDENT_INFO[0]
        self.login(email, password)
        self.enroll(self.course, True)

        resp = self.client.get(reverse('root'), HTTP_HOST=MICROSITE_TEST_HOSTNAME)
        self.assertEquals(resp.status_code, 302)

    def test_microsite_course_enrollment(self):
        """
        Enroll user in a course scoped in a Microsite and one course outside of a Microsite
        and make sure that they are only visible in the right Dashboards
        """
        self.setup_users()

        email, password = self.STUDENT_INFO[1]
        self.login(email, password)
        self.enroll(self.course, True)
        self.enroll(self.course_outside_microsite, True)

        # Access the microsite dashboard and make sure the right courses appear
        resp = self.client.get(reverse('dashboard'), HTTP_HOST=MICROSITE_TEST_HOSTNAME)
        self.assertContains(resp, 'Robot_Super_Course')
        self.assertNotContains(resp, 'Robot_Course_Outside_Microsite')

        # Now access the non-microsite dashboard and make sure the right courses appear
        resp = self.client.get(reverse('dashboard'))
        self.assertNotContains(resp, 'Robot_Super_Course')
        self.assertContains(resp, 'Robot_Course_Outside_Microsite')
