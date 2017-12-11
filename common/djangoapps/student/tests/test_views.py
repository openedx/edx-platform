"""
Test the student dashboard view.
"""
import datetime
import itertools
import json
import unittest

import ddt
import pytz
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase
from edx_oauth2_provider.constants import AUTHORIZED_CLIENTS_SESSION_KEY
from edx_oauth2_provider.tests.factories import ClientFactory, TrustedClientFactory
from milestones.tests.utils import MilestonesTestCaseMixin
from mock import patch
from opaque_keys import InvalidKeyError
from pyquery import PyQuery as pq

from entitlements.tests.factories import CourseEntitlementFactory
from openedx.core.djangoapps.catalog.tests.factories import ProgramFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from student.cookies import get_user_info_cookie_data
from student.helpers import DISABLE_UNENROLL_CERT_STATES
from student.models import CourseEnrollment, UserProfile
from student.signals import REFUND_ORDER
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from util.milestones_helpers import get_course_milestones, remove_prerequisite_course, set_prerequisite_courses
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

PASSWORD = 'test'


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestStudentDashboardUnenrollments(SharedModuleStoreTestCase):
    """
    Test to ensure that the student dashboard does not show the unenroll button for users with certificates.
    """
    UNENROLL_ELEMENT_ID = "#actions-item-unenroll-0"

    @classmethod
    def setUpClass(cls):
        super(TestStudentDashboardUnenrollments, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        """ Create a course and user, then log in. """
        super(TestStudentDashboardUnenrollments, self).setUp()
        self.user = UserFactory()
        self.enrollment = CourseEnrollmentFactory(course_id=self.course.id, user=self.user)
        self.cert_status = 'processing'
        self.client.login(username=self.user.username, password=PASSWORD)

    def mock_cert(self, _user, _course_overview, _course_mode):
        """ Return a preset certificate status. """
        return {
            'status': self.cert_status,
            'can_unenroll': self.cert_status not in DISABLE_UNENROLL_CERT_STATES,
            'download_url': 'fake_url',
            'linked_in_url': False,
            'grade': 100,
            'show_survey_button': False
        }

    @ddt.data(
        ('notpassing', 1),
        ('restricted', 1),
        ('processing', 1),
        ('generating', 0),
        ('downloadable', 0),
    )
    @ddt.unpack
    def test_unenroll_available(self, cert_status, unenroll_action_count):
        """ Assert that the unenroll action is shown or not based on the cert status."""
        self.cert_status = cert_status

        with patch('student.views.cert_info', side_effect=self.mock_cert):
            response = self.client.get(reverse('dashboard'))

            self.assertEqual(pq(response.content)(self.UNENROLL_ELEMENT_ID).length, unenroll_action_count)

    @ddt.data(
        ('notpassing', 200),
        ('restricted', 200),
        ('processing', 200),
        ('generating', 400),
        ('downloadable', 400),
    )
    @ddt.unpack
    @patch.object(CourseEnrollment, 'unenroll')
    def test_unenroll_request(self, cert_status, status_code, course_enrollment):
        """ Assert that the unenroll method is called or not based on the cert status"""
        self.cert_status = cert_status

        with patch('student.views.cert_info', side_effect=self.mock_cert):
            with patch('lms.djangoapps.commerce.signals.handle_refund_order') as mock_refund_handler:
                REFUND_ORDER.connect(mock_refund_handler)
                response = self.client.post(
                    reverse('change_enrollment'),
                    {'enrollment_action': 'unenroll', 'course_id': self.course.id}
                )

                self.assertEqual(response.status_code, status_code)
                if status_code == 200:
                    course_enrollment.assert_called_with(self.user, self.course.id)
                    self.assertTrue(mock_refund_handler.called)
                else:
                    course_enrollment.assert_not_called()

    def test_cant_unenroll_status(self):
        """ Assert that the dashboard loads when cert_status does not allow for unenrollment"""
        with patch('certificates.models.certificate_status_for_student', return_value={'status': 'downloadable'}):
            response = self.client.get(reverse('dashboard'))

            self.assertEqual(response.status_code, 200)

    def test_course_run_refund_status_successful(self):
        """ Assert that view:course_run_refund_status returns correct Json for successful refund call."""
        with patch('student.models.CourseEnrollment.refundable', return_value=True):
            response = self.client.get(reverse('course_run_refund_status', kwargs={'course_id': self.course.id}))

        self.assertEquals(json.loads(response.content), {'course_refundable_status': True})
        self.assertEqual(response.status_code, 200)

        with patch('student.models.CourseEnrollment.refundable', return_value=False):
            response = self.client.get(reverse('course_run_refund_status', kwargs={'course_id': self.course.id}))

        self.assertEquals(json.loads(response.content), {'course_refundable_status': False})
        self.assertEqual(response.status_code, 200)

    def test_course_run_refund_status_invalid_course_key(self):
        """ Assert that view:course_run_refund_status returns correct Json for Invalid Course Key ."""
        with patch('opaque_keys.edx.keys.CourseKey.from_string') as mock_method:
            mock_method.side_effect = InvalidKeyError('CourseKey', 'The course key used to get refund status caused \
                                                        InvalidKeyError during look up.')
            response = self.client.get(reverse('course_run_refund_status', kwargs={'course_id': self.course.id}))

        self.assertEquals(json.loads(response.content), {'course_refundable_status': ''})
        self.assertEqual(response.status_code, 406)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class LogoutTests(TestCase):
    """ Tests for the logout functionality. """

    def setUp(self):
        """ Create a course and user, then log in. """
        super(LogoutTests, self).setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=PASSWORD)

    def create_oauth_client(self):
        """ Creates a trusted OAuth client. """
        client = ClientFactory(logout_uri='https://www.example.com/logout/')
        TrustedClientFactory(client=client)
        return client

    def assert_session_logged_out(self, oauth_client, **logout_headers):
        """ Authenticates a user via OAuth 2.0, logs out, and verifies the session is logged out. """
        self.authenticate_with_oauth(oauth_client)

        # Logging out should remove the session variables, and send a list of logout URLs to the template.
        # The template will handle loading those URLs and redirecting the user. That functionality is not tested here.
        response = self.client.get(reverse('logout'), **logout_headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(AUTHORIZED_CLIENTS_SESSION_KEY, self.client.session)

        return response

    def authenticate_with_oauth(self, oauth_client):
        """ Perform an OAuth authentication using the current web client.

        This should add an AUTHORIZED_CLIENTS_SESSION_KEY entry to the current session.
        """
        data = {
            'client_id': oauth_client.client_id,
            'client_secret': oauth_client.client_secret,
            'response_type': 'code'
        }
        # Authenticate with OAuth to set the appropriate session values
        self.client.post(reverse('oauth2:capture'), data, follow=True)
        self.assertListEqual(self.client.session[AUTHORIZED_CLIENTS_SESSION_KEY], [oauth_client.client_id])

    def assert_logout_redirects_to_root(self):
        """ Verify logging out redirects the user to the homepage. """
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def assert_logout_redirects_with_target(self):
        """ Verify logging out with a redirect_url query param redirects the user to the target. """
        url = '{}?{}'.format(reverse('logout'), 'redirect_url=/courses')
        response = self.client.get(url)
        self.assertRedirects(response, '/courses', fetch_redirect_response=False)

    def test_without_session_value(self):
        """ Verify logout works even if the session does not contain an entry with
        the authenticated OpenID Connect clients."""
        self.assert_logout_redirects_to_root()
        self.assert_logout_redirects_with_target()

    def test_client_logout(self):
        """ Verify the context includes a list of the logout URIs of the authenticated OpenID Connect clients.

        The list should only include URIs of the clients for which the user has been authenticated.
        """
        client = self.create_oauth_client()
        response = self.assert_session_logged_out(client)
        expected = {
            'logout_uris': [client.logout_uri + '?no_redirect=1'],  # pylint: disable=no-member
            'target': '/',
        }
        self.assertDictContainsSubset(expected, response.context_data)  # pylint: disable=no-member

    def test_filter_referring_service(self):
        """ Verify that, if the user is directed to the logout page from a service, that service's logout URL
        is not included in the context sent to the template.
        """
        client = self.create_oauth_client()
        response = self.assert_session_logged_out(client, HTTP_REFERER=client.logout_uri)  # pylint: disable=no-member
        expected = {
            'logout_uris': [],
            'target': '/',
        }
        self.assertDictContainsSubset(expected, response.context_data)  # pylint: disable=no-member


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class StudentDashboardTests(SharedModuleStoreTestCase, MilestonesTestCaseMixin):
    """
    Tests for the student dashboard.
    """

    ENABLED_SIGNALS = ['course_published']
    TOMORROW = datetime.datetime.now(pytz.utc) + datetime.timedelta(days=1)
    MOCK_SETTINGS = {
        'FEATURES': {
            'DISABLE_START_DATES': False,
            'ENABLE_MKTG_SITE': True
        },
        'SOCIAL_SHARING_SETTINGS': {
            'CUSTOM_COURSE_URLS': True,
            'DASHBOARD_FACEBOOK': True,
            'DASHBOARD_TWITTER': True,
        },
    }

    def setUp(self):
        """
        Create a course and user, then log in.
        """
        super(StudentDashboardTests, self).setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=PASSWORD)
        self.path = reverse('dashboard')

    def set_course_sharing_urls(self, set_marketing, set_social_sharing):
        """
        Set course sharing urls (i.e. social_sharing_url, marketing_url)
        """
        course_overview = self.course_enrollment.course_overview
        if set_marketing:
            course_overview.marketing_url = 'http://www.testurl.com/marketing/url/'

        if set_social_sharing:
            course_overview.social_sharing_url = 'http://www.testurl.com/social/url/'

        course_overview.save()

    def test_user_info_cookie(self):
        """
        Verify visiting the learner dashboard sets the user info cookie.
        """
        self.assertNotIn(settings.EDXMKTG_USER_INFO_COOKIE_NAME, self.client.cookies)

        request = RequestFactory().get(self.path)
        request.user = self.user
        expected = json.dumps(get_user_info_cookie_data(request))
        self.client.get(self.path)
        actual = self.client.cookies[settings.EDXMKTG_USER_INFO_COOKIE_NAME].value
        self.assertEqual(actual, expected)

    def test_redirect_account_settings(self):
        """
        Verify if user does not have profile he/she is redirected to account_settings.
        """
        UserProfile.objects.get(user=self.user).delete()
        response = self.client.get(self.path)
        self.assertRedirects(response, reverse('account_settings'))

    @patch.multiple('django.conf.settings', **MOCK_SETTINGS)
    @ddt.data(
        *itertools.product(
            [True, False],
            [True, False],
            [ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split],
        )
    )
    @ddt.unpack
    def test_sharing_icons_for_future_course(self, set_marketing, set_social_sharing, modulestore_type):
        """
        Verify that the course sharing icons show up if course is starting in future and
        any of marketing or social sharing urls are set.
        """
        self.course = CourseFactory.create(start=self.TOMORROW, emit_signals=True, default_store=modulestore_type)
        self.course_enrollment = CourseEnrollmentFactory(course_id=self.course.id, user=self.user)
        self.set_course_sharing_urls(set_marketing, set_social_sharing)

        # Assert course sharing icons
        response = self.client.get(reverse('dashboard'))
        self.assertEqual('Share on Twitter' in response.content, set_marketing or set_social_sharing)
        self.assertEqual('Share on Facebook' in response.content, set_marketing or set_social_sharing)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_PREREQUISITE_COURSES': True})
    def test_pre_requisites_appear_on_dashboard(self):
        """
        When a course has a prerequisite, the dashboard should display the prerequisite.
        If we remove the prerequisite and access the dashboard again, the prerequisite
        should not appear.
        """
        self.pre_requisite_course = CourseFactory.create(org='edx', number='999', display_name='Pre requisite Course')
        self.course = CourseFactory.create(
            org='edx',
            number='998',
            display_name='Test Course',
            pre_requisite_courses=[unicode(self.pre_requisite_course.id)]
        )
        self.course_enrollment = CourseEnrollmentFactory(course_id=self.course.id, user=self.user)

        set_prerequisite_courses(self.course.id, [unicode(self.pre_requisite_course.id)])
        response = self.client.get(reverse('dashboard'))
        self.assertIn('<div class="prerequisites">', response.content)

        remove_prerequisite_course(self.course.id, get_course_milestones(self.course.id)[0])
        response = self.client.get(reverse('dashboard'))
        self.assertNotIn('<div class="prerequisites">', response.content)

    @patch('openedx.core.djangoapps.programs.utils.get_programs')
    @patch('student.views.get_course_runs_for_course')
    @patch.object(CourseOverview, 'get_from_id')
    def test_unfulfilled_entitlement(self, mock_course_overview, mock_course_runs, mock_get_programs):
        """
        When a learner has an unfulfilled entitlement, their course dashboard should have:
            - a hidden 'View Course' button
            - the text 'In order to view the course you must select a session:'
            - an unhidden course-entitlement-selection-container
            - a related programs message
        """
        program = ProgramFactory()
        CourseEntitlementFactory(user=self.user, course_uuid=program['courses'][0]['uuid'])
        mock_get_programs.return_value = [program]
        mock_course_overview.return_value = CourseOverviewFactory(start=self.TOMORROW)
        mock_course_runs.return_value = [
            {
                'key': 'course-v1:FAKE+FA1-MA1.X+3T2017',
                'enrollment_end': self.TOMORROW,
                'pacing_type': 'instructor_paced',
                'type': 'verified'
            }
        ]
        response = self.client.get(self.path)
        self.assertIn('class="enter-course hidden"', response.content)
        self.assertIn('You must select a session to access the course.', response.content)
        self.assertIn('<div class="course-entitlement-selection-container ">', response.content)
        self.assertIn('Related Programs:', response.content)

    @patch('student.views.get_course_runs_for_course')
    @patch.object(CourseOverview, 'get_from_id')
    @patch('opaque_keys.edx.keys.CourseKey.from_string')
    def test_fulfilled_entitlement(self, mock_course_key, mock_course_overview, mock_course_runs):
        """
        When a learner has a fulfilled entitlement, their course dashboard should have:
            - exactly one course item, meaning it:
                - has an entitlement card
                - does NOT have a course card referencing the selected session
            - an unhidden Change Session button
        """
        mocked_course_overview = CourseOverviewFactory(
            start=self.TOMORROW, self_paced=True, enrollment_end=self.TOMORROW
        )
        mock_course_overview.return_value = mocked_course_overview
        mock_course_key.return_value = mocked_course_overview.id
        course_enrollment = CourseEnrollmentFactory(user=self.user, course_id=unicode(mocked_course_overview.id))
        mock_course_runs.return_value = [
            {
                'key': mocked_course_overview.id,
                'enrollment_end': mocked_course_overview.enrollment_end,
                'pacing_type': 'self_paced',
                'type': 'verified'
            }
        ]
        CourseEntitlementFactory(user=self.user, enrollment_course_run=course_enrollment)
        response = self.client.get(self.path)
        self.assertEqual(response.content.count('<li class="course-item">'), 1)
        self.assertIn('<button class="change-session btn-link "', response.content)
