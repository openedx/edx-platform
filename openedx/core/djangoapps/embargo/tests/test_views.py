"""Tests for embargo app views. """


import ddt
import maxminddb
import geoip2.database

from django.urls import reverse
from django.conf import settings
from mock import patch, MagicMock

from .factories import CountryAccessRuleFactory, RestrictedCourseFactory
from .. import messages
from lms.djangoapps.course_api.tests.mixins import CourseApiFactoryMixin
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from openedx.core.djangoapps.theming.tests.test_util import with_comprehensive_theme
from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.util.testing import UrlResetMixin
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@skip_unless_lms
@ddt.ddt
class CourseAccessMessageViewTest(CacheIsolationTestCase, UrlResetMixin):
    """Tests for the courseware access message view.

    These end-points serve static content.
    While we *could* check the text on each page,
    this will require changes to the test every time
    the text on the page changes.

    Instead, we load each page we expect to be available
    (based on the configuration in `embargo.messages`)
    and verify that we get the correct status code.

    This will catch errors in the message configuration
    (for example, moving a template and forgetting to
    update the configuration appropriately).

    """

    ENABLED_CACHES = ['default']

    URLCONF_MODULES = ['openedx.core.djangoapps.embargo']

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):
        super(CourseAccessMessageViewTest, self).setUp()

    @ddt.data(*list(messages.ENROLL_MESSAGES.keys()))
    def test_enrollment_messages(self, msg_key):
        self._load_page('enrollment', msg_key)

    @ddt.data(*list(messages.COURSEWARE_MESSAGES.keys()))
    def test_courseware_messages(self, msg_key):
        self._load_page('courseware', msg_key)

    @ddt.data('enrollment', 'courseware')
    def test_invalid_message_key(self, access_point):
        self._load_page(access_point, 'invalid', expected_status=404)

    @with_comprehensive_theme("test-theme")
    @ddt.data('enrollment', 'courseware')
    def test_custom_theme_override(self, access_point):
        # Custom override specified for the "embargo" message
        # for backwards compatibility with previous versions
        # of the embargo app.
        url = reverse('embargo:blocked_message', kwargs={
            'access_point': access_point,
            'message_key': "embargo"
        })
        response = self.client.get(url)
        self.assertContains(
            response,
            "This is a test template to test embargo message override for theming."
        )

    def _load_page(self, access_point, message_key, expected_status=200):
        """Load the message page and check the status code. """
        url = reverse('embargo:blocked_message', kwargs={
            'access_point': access_point,
            'message_key': message_key
        })
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, expected_status,
            msg=(
                u"Unexpected status code when loading '{url}': "
                u"expected {expected} but got {actual}"
            ).format(
                url=url,
                expected=expected_status,
                actual=response.status_code
            )
        )


@skip_unless_lms
class CheckCourseAccessViewTest(CourseApiFactoryMixin, ModuleStoreTestCase):
    """ Tests the course access check endpoint. """

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):
        super(CheckCourseAccessViewTest, self).setUp()
        self.url = reverse('api_embargo:v1_course_access')
        user = UserFactory(is_staff=True)
        self.client.login(username=user.username, password=UserFactory._DEFAULT_PASSWORD)
        self.course_id = str(CourseFactory().id)
        self.request_data = {
            'course_ids': [self.course_id],
            'ip_address': '0.0.0.0',
            'user': self.user,
        }

    def test_course_access_endpoint_with_unrestricted_course(self):
        response = self.client.get(self.url, data=self.request_data)
        expected_response = {'access': True}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_response)

    def test_course_access_endpoint_with_restricted_course(self):
        CountryAccessRuleFactory(restricted_course=RestrictedCourseFactory(course_key=self.course_id))

        self.user.is_staff = False
        self.user.save()
        # Appear to make a request from an IP in the blocked country

        # pylint: disable=unused-argument
        def mock_country(reader, country):
            """
            :param reader:
            :param country:
            :return:
            """
            magic_mock = MagicMock()
            magic_mock.country = MagicMock()
            type(magic_mock.country).iso_code = 'US'

            return magic_mock

        patcher = patch.object(maxminddb, 'open_database')
        patcher.start()
        country_patcher = patch.object(geoip2.database.Reader, 'country', mock_country)
        country_patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(country_patcher.stop)

        response = self.client.get(self.url, data=self.request_data)

        expected_response = {'access': False}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_response)

    def test_course_access_endpoint_with_logged_out_user(self):
        self.client.logout()
        response = self.client.get(self.url, data=self.request_data)
        self.assertEqual(response.status_code, 403)

    def test_course_access_endpoint_with_non_staff_user(self):
        user = UserFactory(is_staff=False)
        self.client.login(username=user.username, password=UserFactory._DEFAULT_PASSWORD)

        response = self.client.get(self.url, data=self.request_data)
        self.assertEqual(response.status_code, 403)

    def test_course_access_endpoint_with_invalid_data(self):
        response = self.client.get(self.url, data=None)
        self.assertEqual(response.status_code, 400)

    def test_invalid_course_id(self):
        self.request_data['course_ids'] = ['foo']
        response = self.client.get(self.url, data=self.request_data)
        self.assertEqual(response.status_code, 400)
