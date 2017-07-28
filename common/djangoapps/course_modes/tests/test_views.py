"""
Tests for course_modes views.
"""

import decimal
import unittest
from datetime import datetime

import ddt
import freezegun
import httpretty
from django.conf import settings
from django.core.urlresolvers import reverse
from mock import patch
from nose.plugins.attrib import attr

from course_modes.models import CourseMode, Mode
from course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.commerce.tests import test_utils as ecomm_test_utils
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from openedx.core.djangoapps.embargo.test_utils import restrict_course
from openedx.core.djangoapps.theming.tests.test_util import with_comprehensive_theme
from openedx.features.enterprise_support.tests.mixins.enterprise import EnterpriseServiceMockMixin
from student.models import CourseEnrollment
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from util import organizations_helpers as organizations_api
from util.testing import UrlResetMixin
from util.tests.mixins.discovery import CourseCatalogServiceMockMixin
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@attr(shard=3)
@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CourseModeViewTest(CatalogIntegrationMixin, UrlResetMixin, ModuleStoreTestCase, EnterpriseServiceMockMixin, CourseCatalogServiceMockMixin):
    """
    Course Mode View tests
    """
    URLCONF_MODULES = ['course_modes.urls']

    @patch.dict(settings.FEATURES, {'MODE_CREATION_FOR_TESTING': True})
    def setUp(self):
        super(CourseModeViewTest, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        self.client.login(username=self.user.username, password="edx")

        # Create a service user, because the track selection page depends on it
        UserFactory.create(
            username='enterprise_worker',
            email="enterprise_worker@example.com",
            password="edx",
        )

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @httpretty.activate
    @ddt.data(
        # is_active?, enrollment_mode, redirect?
        (True, 'verified', True),
        (True, 'honor', False),
        (True, 'audit', False),
        (False, 'verified', False),
        (False, 'honor', False),
        (False, 'audit', False),
        (False, None, False),
    )
    @ddt.unpack
    def test_redirect_to_dashboard(self, is_active, enrollment_mode, redirect):
        # Create the course modes
        for mode in ('audit', 'honor', 'verified'):
            CourseModeFactory.create(mode_slug=mode, course_id=self.course.id)

        # Enroll the user in the test course
        if enrollment_mode is not None:
            CourseEnrollmentFactory(
                is_active=is_active,
                mode=enrollment_mode,
                course_id=self.course.id,
                user=self.user
            )

        self.mock_enterprise_learner_api()

        # Configure whether we're upgrading or not
        url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        response = self.client.get(url)

        # Check whether we were correctly redirected
        if redirect:
            self.assertRedirects(response, reverse('dashboard'))
        else:
            self.assertEquals(response.status_code, 200)

    def test_no_id_redirect(self):
        # Create the course modes
        CourseModeFactory.create(mode_slug=CourseMode.NO_ID_PROFESSIONAL_MODE, course_id=self.course.id, min_price=100)

        # Enroll the user in the test course
        CourseEnrollmentFactory(
            is_active=False,
            mode=CourseMode.NO_ID_PROFESSIONAL_MODE,
            course_id=self.course.id,
            user=self.user
        )

        # Configure whether we're upgrading or not
        url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        response = self.client.get(url)
        # Check whether we were correctly redirected
        purchase_workflow = "?purchase_workflow=single"
        start_flow_url = reverse('verify_student_start_flow', args=[unicode(self.course.id)]) + purchase_workflow
        self.assertRedirects(response, start_flow_url)

    def test_no_id_redirect_otto(self):
        # Create the course modes
        prof_course = CourseFactory.create()
        CourseModeFactory(mode_slug=CourseMode.NO_ID_PROFESSIONAL_MODE, course_id=prof_course.id,
                          min_price=100, sku='TEST', bulk_sku="BULKTEST")
        ecomm_test_utils.update_commerce_config(enabled=True)
        # Enroll the user in the test course
        CourseEnrollmentFactory(
            is_active=False,
            mode=CourseMode.NO_ID_PROFESSIONAL_MODE,
            course_id=prof_course.id,
            user=self.user
        )
        # Configure whether we're upgrading or not
        url = reverse('course_modes_choose', args=[unicode(prof_course.id)])
        response = self.client.get(url)
        self.assertRedirects(response, 'http://testserver/basket/add/?sku=TEST', fetch_redirect_response=False)
        ecomm_test_utils.update_commerce_config(enabled=False)

    def _generate_enterprise_learner_context(self, enable_audit_enrollment=False):
        """
        Internal helper to support common pieces of test case variations
        """
        # Create the course modes
        for mode in ('audit', 'honor', 'verified'):
            CourseModeFactory.create(mode_slug=mode, course_id=self.course.id)

        catalog_integration = self.create_catalog_integration()
        UserFactory(username=catalog_integration.service_username)

        self.mock_course_discovery_api_for_catalog_contains(
            catalog_id=1, course_run_ids=[str(self.course.id)]
        )
        self.mock_enterprise_learner_api(enable_audit_enrollment=enable_audit_enrollment)

        return reverse('course_modes_choose', args=[unicode(self.course.id)])

    @httpretty.activate
    def test_no_enrollment(self):
        url = self._generate_enterprise_learner_context()
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    @httpretty.activate
    def test_enterprise_learner_context(self):
        """
        Test: Track selection page should show the enterprise context message if user belongs to the Enterprise.
        """
        url = self._generate_enterprise_learner_context()

        # User visits the track selection page directly without ever enrolling
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(
            response,
            'Welcome, {username}! You are about to enroll in {course_name}, from {partner_names}, '
            'sponsored by TestShib. Please select your enrollment information below.'.format(
                username=self.user.username,
                course_name=self.course.display_name_with_default_escaped,
                partner_names=self.course.org
            )
        )

    @httpretty.activate
    def test_enterprise_learner_context_with_multiple_organizations(self):
        """
        Test: Track selection page should show the enterprise context message with multiple organization names
        if user belongs to the Enterprise.
        """
        url = self._generate_enterprise_learner_context()

        # Creating organization
        for i in xrange(2):
            test_organization_data = {
                'name': 'test organization ' + str(i),
                'short_name': 'test_organization_' + str(i),
                'description': 'Test Organization Description',
                'active': True,
                'logo': '/logo_test1.png/'
            }
            test_org = organizations_api.add_organization(organization_data=test_organization_data)
            organizations_api.add_organization_course(organization_data=test_org, course_id=unicode(self.course.id))

        # User visits the track selection page directly without ever enrolling
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(
            response,
            'Welcome, {username}! You are about to enroll in {course_name}, from test organization 0 and '
            'test organization 1, sponsored by TestShib. Please select your enrollment information below.'.format(
                username=self.user.username,
                course_name=self.course.display_name_with_default_escaped
            )
        )

    @httpretty.activate
    def test_enterprise_learner_context_audit_disabled(self):
        """
        Track selection page should hide the audit choice by default in an Enterprise Customer/Learner context
        """

        # User visits the track selection page directly without ever enrolling, sees only Verified track choice
        url = self._generate_enterprise_learner_context()
        response = self.client.get(url)
        self.assertContains(response, 'Pursue a Verified Certificate')
        self.assertNotContains(response, 'Audit This Course')

    @httpretty.activate
    def test_enterprise_learner_context_audit_enabled(self):
        """
        Track selection page should display Audit choice when specified for an Enterprise Customer
        """

        # User visits the track selection page directly without ever enrolling, sees both Verified and Audit choices
        url = self._generate_enterprise_learner_context(enable_audit_enrollment=True)
        response = self.client.get(url)
        self.assertContains(response, 'Pursue a Verified Certificate')
        self.assertContains(response, 'Audit This Course')

    @httpretty.activate
    @ddt.data(
        '',
        '1,,2',
        '1, ,2',
        '1, 2, 3'
    )
    def test_suggested_prices(self, price_list):

        # Create the course modes
        for mode in ('audit', 'honor'):
            CourseModeFactory.create(mode_slug=mode, course_id=self.course.id)

        CourseModeFactory.create(
            mode_slug='verified',
            course_id=self.course.id,
            suggested_prices=price_list
        )

        # Enroll the user in the test course to emulate
        # automatic enrollment
        CourseEnrollmentFactory(
            is_active=True,
            course_id=self.course.id,
            user=self.user
        )

        self.mock_enterprise_learner_api()

        # Verify that the prices render correctly
        response = self.client.get(
            reverse('course_modes_choose', args=[unicode(self.course.id)]),
            follow=False,
        )

        self.assertEquals(response.status_code, 200)
        # TODO: Fix it so that response.templates works w/ mako templates, and then assert
        # that the right template rendered

    @httpretty.activate
    @ddt.data(
        (['honor', 'verified', 'credit'], True),
        (['honor', 'verified'], False),
    )
    @ddt.unpack
    def test_credit_upsell_message(self, available_modes, show_upsell):
        # Create the course modes
        for mode in available_modes:
            CourseModeFactory.create(mode_slug=mode, course_id=self.course.id)

        self.mock_enterprise_learner_api()

        # Check whether credit upsell is shown on the page
        # This should *only* be shown when a credit mode is available
        url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        response = self.client.get(url)

        if show_upsell:
            self.assertContains(response, "Credit")
        else:
            self.assertNotContains(response, "Credit")

    @ddt.data('professional', 'no-id-professional')
    def test_professional_enrollment(self, mode):
        # The only course mode is professional ed
        CourseModeFactory.create(mode_slug=mode, course_id=self.course.id, min_price=1)

        # Go to the "choose your track" page
        choose_track_url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        response = self.client.get(choose_track_url)

        # Since the only available track is professional ed, expect that
        # we're redirected immediately to the start of the payment flow.
        purchase_workflow = "?purchase_workflow=single"
        start_flow_url = reverse('verify_student_start_flow', args=[unicode(self.course.id)]) + purchase_workflow
        self.assertRedirects(response, start_flow_url)

        # Now enroll in the course
        CourseEnrollmentFactory(
            user=self.user,
            is_active=True,
            mode=mode,
            course_id=unicode(self.course.id),
        )

        # Expect that this time we're redirected to the dashboard (since we're already registered)
        response = self.client.get(choose_track_url)
        self.assertRedirects(response, reverse('dashboard'))

    # Mapping of course modes to the POST parameters sent
    # when the user chooses that mode.
    POST_PARAMS_FOR_COURSE_MODE = {
        'audit': {'audit_mode': True},
        'honor': {'honor_mode': True},
        'verified': {'verified_mode': True, 'contribution': '1.23'},
        'unsupported': {'unsupported_mode': True},
    }

    @ddt.data(
        ('audit', 'dashboard'),
        ('honor', 'dashboard'),
        ('verified', 'start-flow'),
    )
    @ddt.unpack
    def test_choose_mode_redirect(self, course_mode, expected_redirect):
        # Create the course modes
        for mode in ('audit', 'honor', 'verified'):
            min_price = 0 if mode in ["honor", "audit"] else 1
            CourseModeFactory.create(mode_slug=mode, course_id=self.course.id, min_price=min_price)

        # Choose the mode (POST request)
        choose_track_url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        response = self.client.post(choose_track_url, self.POST_PARAMS_FOR_COURSE_MODE[course_mode])

        # Verify the redirect
        if expected_redirect == 'dashboard':
            redirect_url = reverse('dashboard')
        elif expected_redirect == 'start-flow':
            redirect_url = reverse(
                'verify_student_start_flow',
                kwargs={'course_id': unicode(self.course.id)}
            )
        else:
            self.fail("Must provide a valid redirect URL name")

        self.assertRedirects(response, redirect_url)

    def test_choose_mode_audit_enroll_on_post(self):
        audit_mode = 'audit'
        # Create the course modes
        for mode in (audit_mode, 'verified'):
            min_price = 0 if mode in [audit_mode] else 1
            CourseModeFactory.create(mode_slug=mode, course_id=self.course.id, min_price=min_price)

        # Assert learner is not enrolled in Audit track pre-POST
        mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertIsNone(mode)
        self.assertIsNone(is_active)

        # Choose the audit mode (POST request)
        choose_track_url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        self.client.post(choose_track_url, self.POST_PARAMS_FOR_COURSE_MODE[audit_mode])

        # Assert learner is enrolled in Audit track post-POST
        mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertEqual(mode, audit_mode)
        self.assertTrue(is_active)

        # Unenroll learner from Audit track and confirm the enrollment record is now 'inactive'
        CourseEnrollment.unenroll(self.user, self.course.id)
        mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertEqual(mode, audit_mode)
        self.assertFalse(is_active)

        # Choose the audit mode again
        self.client.post(choose_track_url, self.POST_PARAMS_FOR_COURSE_MODE[audit_mode])

        # Assert learner is again enrolled in Audit track post-POST-POST
        mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertEqual(mode, audit_mode)
        self.assertTrue(is_active)

    def test_remember_donation_for_course(self):
        # Create the course modes
        CourseModeFactory.create(mode_slug='honor', course_id=self.course.id)
        CourseModeFactory.create(mode_slug='verified', course_id=self.course.id, min_price=1)

        # Choose the mode (POST request)
        choose_track_url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        self.client.post(choose_track_url, self.POST_PARAMS_FOR_COURSE_MODE['verified'])

        # Expect that the contribution amount is stored in the user's session
        self.assertIn('donation_for_course', self.client.session)
        self.assertIn(unicode(self.course.id), self.client.session['donation_for_course'])

        actual_amount = self.client.session['donation_for_course'][unicode(self.course.id)]
        expected_amount = decimal.Decimal(self.POST_PARAMS_FOR_COURSE_MODE['verified']['contribution'])
        self.assertEqual(actual_amount, expected_amount)

    def test_successful_default_enrollment(self):
        # Create the course modes
        for mode in (CourseMode.DEFAULT_MODE_SLUG, 'verified'):
            CourseModeFactory.create(mode_slug=mode, course_id=self.course.id)

        # Enroll the user in the default mode (honor) to emulate
        # automatic enrollment
        params = {
            'enrollment_action': 'enroll',
            'course_id': unicode(self.course.id)
        }
        self.client.post(reverse('change_enrollment'), params)

        # Explicitly select the honor mode (POST request)
        choose_track_url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        self.client.post(choose_track_url, self.POST_PARAMS_FOR_COURSE_MODE[CourseMode.DEFAULT_MODE_SLUG])

        # Verify that the user's enrollment remains unchanged
        mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertEqual(mode, CourseMode.DEFAULT_MODE_SLUG)
        self.assertEqual(is_active, True)

    def test_unsupported_enrollment_mode_failure(self):
        # Create the supported course modes
        for mode in ('honor', 'verified'):
            CourseModeFactory.create(mode_slug=mode, course_id=self.course.id)

        # Choose an unsupported mode (POST request)
        choose_track_url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        response = self.client.post(choose_track_url, self.POST_PARAMS_FOR_COURSE_MODE['unsupported'])

        self.assertEqual(400, response.status_code)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_default_mode_creation(self):
        # Hit the mode creation endpoint with no querystring params, to create an honor mode
        url = reverse('create_mode', args=[unicode(self.course.id)])
        response = self.client.get(url)

        self.assertEquals(response.status_code, 200)

        expected_mode = [Mode(u'honor', u'Honor Code Certificate', 0, '', 'usd', None, None, None, None)]
        course_mode = CourseMode.modes_for_course(self.course.id)

        self.assertEquals(course_mode, expected_mode)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @ddt.data(
        (u'verified', u'Verified Certificate', 10, '10,20,30', 'usd'),
        (u'professional', u'Professional Education', 100, '100,200', 'usd'),
    )
    @ddt.unpack
    def test_verified_mode_creation(self, mode_slug, mode_display_name, min_price, suggested_prices, currency):
        parameters = {}
        parameters['mode_slug'] = mode_slug
        parameters['mode_display_name'] = mode_display_name
        parameters['min_price'] = min_price
        parameters['suggested_prices'] = suggested_prices
        parameters['currency'] = currency

        url = reverse('create_mode', args=[unicode(self.course.id)])
        response = self.client.get(url, parameters)

        self.assertEquals(response.status_code, 200)

        expected_mode = [
            Mode(
                mode_slug,
                mode_display_name,
                min_price,
                suggested_prices,
                currency,
                None,
                None,
                None,
                None
            )
        ]
        course_mode = CourseMode.modes_for_course(self.course.id)

        self.assertEquals(course_mode, expected_mode)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_multiple_mode_creation(self):
        # Create an honor mode
        base_url = reverse('create_mode', args=[unicode(self.course.id)])
        self.client.get(base_url)

        # Excluding the currency parameter implicitly tests the mode creation endpoint's ability to
        # use default values when parameters are partially missing.
        parameters = {}
        parameters['mode_slug'] = u'verified'
        parameters['mode_display_name'] = u'Verified Certificate'
        parameters['min_price'] = 10
        parameters['suggested_prices'] = '10,20'

        # Create a verified mode
        url = reverse('create_mode', args=[unicode(self.course.id)])
        self.client.get(url, parameters)

        honor_mode = Mode(u'honor', u'Honor Code Certificate', 0, '', 'usd', None, None, None, None)
        verified_mode = Mode(u'verified', u'Verified Certificate', 10, '10,20', 'usd', None, None, None, None)
        expected_modes = [honor_mode, verified_mode]
        course_modes = CourseMode.modes_for_course(self.course.id)

        self.assertEquals(course_modes, expected_modes)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @with_comprehensive_theme("edx.org")
    @httpretty.activate
    def test_hide_nav(self):
        # Create the course modes
        for mode in ["honor", "verified"]:
            CourseModeFactory.create(mode_slug=mode, course_id=self.course.id)

        self.mock_enterprise_learner_api()

        # Load the track selection page
        url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        response = self.client.get(url)

        # Verify that the header navigation links are hidden for the edx.org version
        self.assertNotContains(response, "How it Works")
        self.assertNotContains(response, "Find courses")
        self.assertNotContains(response, "Schools & Partners")

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_course_closed(self):
        with freezegun.freeze_time('2015-01-02'):
            for mode in ["honor", "verified"]:
                CourseModeFactory(mode_slug=mode, course_id=self.course.id)

            self.course.enrollment_end = datetime(2015, 01, 01)
            modulestore().update_item(self.course, self.user.id)

            url = reverse('course_modes_choose', args=[unicode(self.course.id)])
            response = self.client.get(url)
            # URL-encoded version of 1/1/15, 12:00 AM
            redirect_url = reverse('dashboard') + '?course_closed=1%2F1%2F15%2C+12%3A00+AM'
            self.assertRedirects(response, redirect_url)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TrackSelectionEmbargoTest(UrlResetMixin, ModuleStoreTestCase, EnterpriseServiceMockMixin):
    """Test embargo restrictions on the track selection page. """

    URLCONF_MODULES = ['openedx.core.djangoapps.embargo']

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):
        super(TrackSelectionEmbargoTest, self).setUp()

        # Create a course and course modes
        self.course = CourseFactory.create()
        CourseModeFactory.create(mode_slug='honor', course_id=self.course.id)
        CourseModeFactory.create(mode_slug='verified', course_id=self.course.id, min_price=10)

        # Create a user and log in
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        self.client.login(username=self.user.username, password="edx")

        # Create a service user
        UserFactory.create(
            username='enterprise_worker',
            email="enterprise_worker@example.com",
            password="edx",
        )

        # Construct the URL for the track selection page
        self.url = reverse('course_modes_choose', args=[unicode(self.course.id)])

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_embargo_restrict(self):
        with restrict_course(self.course.id) as redirect_url:
            response = self.client.get(self.url)
            self.assertRedirects(response, redirect_url)

    @httpretty.activate
    def test_embargo_allow(self):

        self.mock_enterprise_learner_api()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
