import ddt
import unittest
from django.conf import settings
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase, mixed_store_config
)

from xmodule.modulestore.tests.factories import CourseFactory
from course_modes.tests.factories import CourseModeFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory


# Since we don't need any XML course fixtures, use a modulestore configuration
# that disables the XML modulestore.
MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@ddt.ddt
@override_settings(MODULESTORE=MODULESTORE_CONFIG)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CourseModeViewTest(ModuleStoreTestCase):

    def setUp(self):
        super(CourseModeViewTest, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        self.client.login(username=self.user.username, password="edx")

    @ddt.data(
        # is_active?, enrollment_mode, upgrade?, redirect? auto_register?
        (True, 'verified', True, True, False),     # User is already verified
        (True, 'verified', False, True, False),    # User is already verified
        (True, 'honor', True, False, False),       # User isn't trying to upgrade
        (True, 'honor', False, True, False),       # User is trying to upgrade
        (True, 'audit', True, False, False),       # User isn't trying to upgrade
        (True, 'audit', False, True, False),       # User is trying to upgrade
        (False, 'verified', True, False, False),   # User isn't active
        (False, 'verified', False, False, False),  # User isn't active
        (False, 'honor', True, False, False),      # User isn't active
        (False, 'honor', False, False, False),     # User isn't active
        (False, 'audit', True, False, False),      # User isn't active
        (False, 'audit', False, False, False),     # User isn't active

        # When auto-registration is enabled, users may already be
        # registered when they reach the "choose your track"
        # page.  In this case, we do NOT want to redirect them
        # to the dashboard, because we want to give them the option
        # to enter the verification/payment track.
        # TODO (ECOM-16): based on the outcome of the auto-registration AB test,
        # either keep these tests or remove them.  In either case,
        # remove the "auto_register" flag from this test case.
        (True, 'verified', True, False, True),
        (True, 'verified', False, True, True),
        (True, 'honor', True, False, True),
        (True, 'honor', False, False, True),
        (True, 'audit', True, False, True),
        (True, 'audit', False, False, True),
    )
    @ddt.unpack
    def test_redirect_to_dashboard(self, is_active, enrollment_mode, upgrade, redirect, auto_register):

        # TODO (ECOM-16): Remove once we complete the auto-reg AB test.
        if auto_register:
            session = self.client.session
            session['auto_register'] = True
            session.save()

        # Create the course modes
        for mode in ('audit', 'honor', 'verified'):
            CourseModeFactory(mode_slug=mode, course_id=self.course.id)

        # Enroll the user in the test course
        CourseEnrollmentFactory(
            is_active=is_active,
            mode=enrollment_mode,
            course_id=self.course.id,
            user=self.user
        )

        # Configure whether we're upgrading or not
        get_params = {}
        if upgrade:
            get_params = {'upgrade': True}

        url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        response = self.client.get(url, get_params)

        # Check whether we were correctly redirected
        if redirect:
            self.assertRedirects(response, reverse('dashboard'))
        else:
            self.assertEquals(response.status_code, 200)

    @ddt.data(
        '',
        '1,,2',
        '1, ,2',
        '1, 2, 3'
    )
    def test_suggested_prices(self, price_list):

        # Create the course modes
        for mode in ('audit', 'honor'):
            CourseModeFactory(mode_slug=mode, course_id=self.course.id)

        CourseModeFactory(
            mode_slug='verified',
            course_id=self.course.id,
            suggested_prices=price_list
        )

        # Verify that the prices render correctly
        response = self.client.get(
            reverse('course_modes_choose', args=[unicode(self.course.id)]),
            follow=False,
        )

        self.assertEquals(response.status_code, 200)
        # TODO: Fix it so that response.templates works w/ mako templates, and then assert
        # that the right template rendered

    # TODO (ECOM-16): Remove the auto-registration flag once the AB test is complete
    # and we choose the winner as the default
    @ddt.data(True, False)
    def test_professional_registration(self, auto_register):

        # TODO (ECOM-16): Remove once we complete the auto-reg AB test.
        if auto_register:
            self.client.session['auto_register'] = True
            self.client.session.save()

        # The only course mode is professional ed
        CourseModeFactory(mode_slug='professional', course_id=self.course.id)

        # Go to the "choose your track" page
        choose_track_url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        response = self.client.get(choose_track_url)

        # Expect that we're redirected immediately to the "show requirements" page
        # (since the only available track is professional ed)
        show_reqs_url = reverse('verify_student_show_requirements', args=[unicode(self.course.id)])
        self.assertRedirects(response, show_reqs_url)

        # Now enroll in the course
        CourseEnrollmentFactory(
            user=self.user,
            is_active=True,
            mode="professional",
            course_id=unicode(self.course.id),
        )

        # Expect that this time we're redirected to the dashboard (since we're already registered)
        response = self.client.get(choose_track_url)
        self.assertRedirects(response, reverse('dashboard'))


    # Mapping of course modes to the POST parameters sent
    # when the user chooses that mode.
    POST_PARAMS_FOR_COURSE_MODE = {
        'audit': {'audit_mode': True},
        'honor': {'honor-code': True},
        'verified': {'certificate_mode': True}
    }

    # TODO (ECOM-16): Remove the auto-register flag once the AB-test completes
    # and we default it to enabled or disabled.
    @ddt.data(
        (False, 'honor', 'dashboard'),
        (False, 'verified', 'show_requirements'),
        (False, 'audit', 'dashboard'),
        (True, 'honor', 'dashboard'),
        (True, 'verified', 'show_requirements'),
        (True, 'audit', 'dashboard'),
    )
    @ddt.unpack
    def test_choose_mode_redirect(self, auto_register, course_mode, expected_redirect):

        # TODO (ECOM-16): Remove once we complete the auto-reg AB test.
        if auto_register:
            self.client.session['auto_register'] = True
            self.client.session.save()

        # Create the course modes
        for mode in ('audit', 'honor', 'verified'):
            CourseModeFactory(mode_slug=mode, course_id=self.course.id)

        # Choose the mode (POST request)
        choose_track_url = reverse('course_modes_choose', args=[unicode(self.course.id)])
        resp = self.client.post(choose_track_url, self.POST_PARAMS_FOR_COURSE_MODE[course_mode])

        # Verify the redirect
        if expected_redirect == 'dashboard':
            redirect_url = reverse('dashboard')
        elif expected_redirect == 'show_requirements':
            redirect_url = reverse(
                'verify_student_show_requirements',
                kwargs={'course_id': unicode(self.course.id)}
            ) + "?upgrade=False"
        else:
            self.fail("Must provide a valid redirect URL name")

        self.assertRedirects(resp, redirect_url)
