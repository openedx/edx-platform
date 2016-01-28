"""
Tests related to the Microsites feature
"""
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from nose.plugins.attrib import attr

from courseware.tests.helpers import LoginEnrollmentTestCase
from course_modes.models import CourseMode
from xmodule.course_module import (
    CATALOG_VISIBILITY_CATALOG_AND_ABOUT, CATALOG_VISIBILITY_NONE)
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@attr('shard_1')
class TestMicrosites(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    This is testing of the Microsite feature
    """

    STUDENT_INFO = [('view@test.com', 'foo'), ('view2@test.com', 'foo')]

    def setUp(self):
        super(TestMicrosites, self).setUp()

        # use a different hostname to test Microsites since they are
        # triggered on subdomain mappings
        #
        # NOTE: The Microsite Configuration is in lms/envs/test.py. The content for the Test Microsite is in
        # test_microsites/test_microsite.
        #
        # IMPORTANT: For these tests to work, this domain must be defined via
        # DNS configuration (either local or published)

        self.course = CourseFactory.create(
            display_name='Robot_Super_Course',
            org='TestMicrositeX',
            emit_signals=True,
        )
        self.chapter0 = ItemFactory.create(parent_location=self.course.location,
                                           display_name='Overview')
        self.chapter9 = ItemFactory.create(parent_location=self.course.location,
                                           display_name='factory_chapter')
        self.section0 = ItemFactory.create(parent_location=self.chapter0.location,
                                           display_name='Welcome')
        self.section9 = ItemFactory.create(parent_location=self.chapter9.location,
                                           display_name='factory_section')

        self.course_outside_microsite = CourseFactory.create(
            display_name='Robot_Course_Outside_Microsite',
            org='FooX',
            emit_signals=True,
        )

        # have a course which explicitly sets visibility in catalog to False
        self.course_hidden_visibility = CourseFactory.create(
            display_name='Hidden_course',
            org='TestMicrositeX',
            catalog_visibility=CATALOG_VISIBILITY_NONE,
            emit_signals=True,
        )

        # have a course which explicitly sets visibility in catalog and about to true
        self.course_with_visibility = CourseFactory.create(
            display_name='visible_course',
            org='TestMicrositeX',
            course="foo",
            catalog_visibility=CATALOG_VISIBILITY_CATALOG_AND_ABOUT,
            emit_signals=True,
        )

    def setup_users(self):
        # Create student accounts and activate them.
        for i in range(len(self.STUDENT_INFO)):
            email, password = self.STUDENT_INFO[i]
            username = 'u{0}'.format(i)
            self.create_account(username, email, password)
            self.activate_user(email)

    @override_settings(SITE_NAME=settings.MICROSITE_TEST_HOSTNAME)
    def test_microsite_anonymous_homepage_content(self):
        """
        Verify that the homepage, when accessed via a Microsite domain, returns
        HTML that reflects the Microsite branding elements
        """

        resp = self.client.get('/', HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEqual(resp.status_code, 200)

        # assert various branding definitions on this Microsite
        # as per the configuration and Microsite overrides

        self.assertContains(resp, 'This is a Test Microsite Overlay')   # Overlay test message
        self.assertContains(resp, 'test_microsite/images/header-logo.png')  # logo swap
        self.assertContains(resp, 'test_microsite/css/test_microsite')  # css override
        self.assertContains(resp, 'Test Microsite')   # page title

        # assert that test course display name is visible
        self.assertContains(resp, 'Robot_Super_Course')

        # assert that test course with 'visible_in_catalog' to True is showing up
        self.assertContains(resp, 'visible_course')

        # assert that test course that is outside microsite is not visible
        self.assertNotContains(resp, 'Robot_Course_Outside_Microsite')

        # assert that a course that has visible_in_catalog=False is not visible
        self.assertNotContains(resp, 'Hidden_course')

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

    @override_settings(SITE_NAME=settings.MICROSITE_TEST_HOSTNAME)
    def test_microsite_anonymous_copyright_content(self):
        """
        Verify that the copyright, when accessed via a Microsite domain, returns
        the expected 200 response
        """

        resp = self.client.get('/copyright', HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEqual(resp.status_code, 200)

        self.assertContains(resp, 'This is a copyright page for an Open edX microsite.')

    def test_not_microsite_anonymous_copyright_content(self):
        """
        Verify that the copyright page does not exist if we are not in a microsite
        """

        resp = self.client.get('/copyright')
        self.assertEqual(resp.status_code, 404)

    def test_no_redirect_on_homepage_when_no_enrollments(self):
        """
        Verify that a user going to homepage will not redirect if he/she has no course enrollments
        """
        self.setup_users()

        email, password = self.STUDENT_INFO[0]
        self.login(email, password)
        resp = self.client.get(reverse('root'), HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEquals(resp.status_code, 200)

    def test_no_redirect_on_homepage_when_has_enrollments(self):
        """
        Verify that a user going to homepage will not redirect to dashboard if he/she has
        a course enrollment
        """
        self.setup_users()

        email, password = self.STUDENT_INFO[0]
        self.login(email, password)
        self.enroll(self.course, True)

        resp = self.client.get(reverse('root'), HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEquals(resp.status_code, 200)

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
        resp = self.client.get(reverse('dashboard'), HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertContains(resp, 'Robot_Super_Course')
        self.assertNotContains(resp, 'Robot_Course_Outside_Microsite')

        # Now access the non-microsite dashboard and make sure the right courses appear
        resp = self.client.get(reverse('dashboard'))
        self.assertNotContains(resp, 'Robot_Super_Course')
        self.assertContains(resp, 'Robot_Course_Outside_Microsite')

    @override_settings(SITE_NAME=settings.MICROSITE_TEST_HOSTNAME)
    def test_visible_about_page_settings(self):
        """
        Make sure the Microsite is honoring the visible_about_page permissions that is
        set in configuration
        """
        url = reverse('about_course', args=[self.course_with_visibility.id.to_deprecated_string()])
        resp = self.client.get(url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEqual(resp.status_code, 200)

        url = reverse('about_course', args=[self.course_hidden_visibility.id.to_deprecated_string()])
        resp = self.client.get(url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEqual(resp.status_code, 404)

    @override_settings(SITE_NAME=settings.MICROSITE_TEST_HOSTNAME)
    def test_paid_course_registration(self):
        """
        Make sure that Microsite overrides on the ENABLE_SHOPPING_CART and
        ENABLE_PAID_COURSE_ENROLLMENTS are honored
        """
        course_mode = CourseMode(
            course_id=self.course_with_visibility.id,
            mode_slug=CourseMode.DEFAULT_MODE_SLUG,
            mode_display_name=CourseMode.DEFAULT_MODE_SLUG,
            min_price=10,
        )
        course_mode.save()

        # first try on the non microsite, which
        # should pick up the global configuration (where ENABLE_PAID_COURSE_REGISTRATIONS = False)
        url = reverse('about_course', args=[self.course_with_visibility.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Enroll in {}".format(self.course_with_visibility.id.course), resp.content)
        self.assertNotIn("Add {} to Cart ($10)".format(self.course_with_visibility.id.course), resp.content)

        # now try on the microsite
        url = reverse('about_course', args=[self.course_with_visibility.id.to_deprecated_string()])
        resp = self.client.get(url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("Enroll in {}".format(self.course_with_visibility.id.course), resp.content)
        self.assertIn("Add {} to Cart <span>($10 USD)</span>".format(
            self.course_with_visibility.id.course
        ), resp.content)
        self.assertIn('$("#add_to_cart_post").click', resp.content)
