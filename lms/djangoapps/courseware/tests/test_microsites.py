"""
Tests related to the Site COnfiguration feature
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
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase


@attr('shard_1')
class TestSites(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    This is testing of the Site Configuration feature
    """

    STUDENT_INFO = [('view@test.com', 'foo'), ('view2@test.com', 'foo')]

    @classmethod
    def setUpClass(cls):
        super(TestSites, cls).setUpClass()
        cls.course = CourseFactory.create(
            display_name='Robot_Super_Course',
            org='TestSiteX',
            emit_signals=True,
        )
        cls.chapter0 = ItemFactory.create(parent_location=cls.course.location, display_name='Overview')
        cls.chapter9 = ItemFactory.create(parent_location=cls.course.location, display_name='factory_chapter')
        cls.section0 = ItemFactory.create(parent_location=cls.chapter0.location, display_name='Welcome')
        cls.section9 = ItemFactory.create(parent_location=cls.chapter9.location, display_name='factory_section')

        cls.course_outside_site = CourseFactory.create(
            display_name='Robot_Course_Outside_Site',
            org='FooX',
            emit_signals=True,
        )

        # have a course which explicitly sets visibility in catalog to False
        cls.course_hidden_visibility = CourseFactory.create(
            display_name='Hidden_course',
            org='TestSiteX',
            catalog_visibility=CATALOG_VISIBILITY_NONE,
            emit_signals=True,
        )

        # have a course which explicitly sets visibility in catalog and about to true
        cls.course_with_visibility = CourseFactory.create(
            display_name='visible_course',
            org='TestSiteX',
            course="foo",
            catalog_visibility=CATALOG_VISIBILITY_CATALOG_AND_ABOUT,
            emit_signals=True,
        )

    def setUp(self):
        super(TestSites, self).setUp()

    def setup_users(self):
        # Create student accounts and activate them.
        for i in range(len(self.STUDENT_INFO)):
            email, password = self.STUDENT_INFO[i]
            username = 'u{0}'.format(i)
            self.create_account(username, email, password)
            self.activate_user(email)

    @override_settings(SITE_NAME=settings.MICROSITE_TEST_HOSTNAME)
    def test_site_anonymous_homepage_content(self):
        """
        Verify that the homepage, when accessed via a Site domain, returns
        HTML that reflects the Site branding elements
        """

        resp = self.client.get('/', HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEqual(resp.status_code, 200)

        # assert various branding definitions on this Site
        # as per the configuration and Site overrides

        self.assertContains(resp, 'This is a Test Site Overlay')   # Overlay test message
        self.assertContains(resp, 'test_site/images/header-logo.png')  # logo swap
        self.assertContains(resp, 'test_site/css/test_site')  # css override
        self.assertContains(resp, 'Test Site')   # page title

        # assert that test course display name is visible
        self.assertContains(resp, 'Robot_Super_Course')

        # assert that test course with 'visible_in_catalog' to True is showing up
        self.assertContains(resp, 'visible_course')

        # assert that test course that is outside current configured site is not visible
        self.assertNotContains(resp, 'Robot_Course_Outside_Site')

        # assert that a course that has visible_in_catalog=False is not visible
        self.assertNotContains(resp, 'Hidden_course')

        # assert that footer template has been properly overriden on homepage
        self.assertContains(resp, 'This is a Test Site footer')

        # assert that the edX partners section is not in the HTML
        self.assertNotContains(resp, '<section class="university-partners university-partners2x6">')

        # assert that the edX partners tag line is not in the HTML
        self.assertNotContains(resp, 'Explore free courses from')

    def test_no_configuration_anonymous_homepage_content(self):
        """
        Make sure we see the right content on the homepage if there is no site configuration defined.
        """

        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

        # assert various branding definitions on this Site ARE NOT VISIBLE

        self.assertNotContains(resp, 'This is a Test Site Overlay')   # Overlay test message
        self.assertNotContains(resp, 'test_site/images/header-logo.png')  # logo swap
        self.assertNotContains(resp, 'test_site/css/test_site')  # css override
        self.assertNotContains(resp, '<title>Test Site</title>')   # page title

        # assert that test course display name IS NOT VISIBLE
        self.assertNotContains(resp, 'Robot_Super_Course')

        # assert that test course that is outside site IS VISIBLE
        self.assertContains(resp, 'Robot_Course_Outside_Site')

        # assert that footer template has been properly overriden on homepage
        self.assertNotContains(resp, 'This is a Test Site footer')

    @override_settings(SITE_NAME=settings.MICROSITE_TEST_HOSTNAME)
    def test_site_anonymous_copyright_content(self):
        """
        Verify that the copyright, when accessed via a Site domain, returns
        the expected 200 response
        """

        resp = self.client.get('/copyright', HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEqual(resp.status_code, 200)

        self.assertContains(resp, 'This is a copyright page for an Open edX site.')

    def test_not_site_anonymous_copyright_content(self):
        """
        Verify that the copyright page does not exist if we are not in a configured site.
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

    def test_site_course_enrollment(self):
        """
        Enroll user in a course scoped in a Site and one course outside of a Site
        and make sure that they are only visible in the right Dashboards
        """
        self.setup_users()

        email, password = self.STUDENT_INFO[1]
        self.login(email, password)
        self.enroll(self.course, True)
        self.enroll(self.course_outside_site, True)

        # Access the site dashboard and make sure the right courses appear
        resp = self.client.get(reverse('dashboard'), HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertContains(resp, 'Robot_Super_Course')
        self.assertNotContains(resp, 'Robot_Course_Outside_Site')

        # Now access the non-site dashboard and make sure the right courses appear
        resp = self.client.get(reverse('dashboard'))
        self.assertNotContains(resp, 'Robot_Super_Course')
        self.assertContains(resp, 'Robot_Course_Outside_Site')

    def test_site_course_custom_tabs(self):
        """
        Enroll user in a course scoped in a Site and make sure that
        template with tabs is overridden
        """
        self.setup_users()

        email, password = self.STUDENT_INFO[1]
        self.login(email, password)
        self.enroll(self.course, True)

        resp = self.client.get(reverse('courseware', args=[unicode(self.course.id)]),
                               HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertContains(resp, 'Test Site Tab:')

    @override_settings(SITE_NAME=settings.MICROSITE_TEST_HOSTNAME)
    def test_visible_about_page_settings(self):
        """
        Make sure the Site is honoring the visible_about_page permissions that is
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
        Make sure that Site overrides on the ENABLE_SHOPPING_CART and
        ENABLE_PAID_COURSE_ENROLLMENTS are honored
        """
        course_mode = CourseMode(
            course_id=self.course_with_visibility.id,
            mode_slug=CourseMode.DEFAULT_MODE_SLUG,
            mode_display_name=CourseMode.DEFAULT_MODE_SLUG,
            min_price=10,
        )
        course_mode.save()

        # first try on the non site, which
        # should pick up the global configuration (where ENABLE_PAID_COURSE_REGISTRATIONS = False)
        url = reverse('about_course', args=[self.course_with_visibility.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Enroll in {}".format(self.course_with_visibility.id.course), resp.content)
        self.assertNotIn("Add {} to Cart ($10)".format(self.course_with_visibility.id.course), resp.content)

        # now try on the site
        url = reverse('about_course', args=[self.course_with_visibility.id.to_deprecated_string()])
        resp = self.client.get(url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("Enroll in {}".format(self.course_with_visibility.id.course), resp.content)
        self.assertIn("Add {} to Cart <span>($10 USD)</span>".format(
            self.course_with_visibility.id.course
        ), resp.content)
        self.assertIn('$("#add_to_cart_post").click', resp.content)
