"""
Tests for EmbargoMiddleware with CountryAccessRules
"""


import ddt
import six
from config_models.models import cache as config_cache
from django.conf import settings
from django.core.cache import cache as django_cache
from django.urls import reverse
from mock import patch

from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.util.testing import UrlResetMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..models import IPFilter, RestrictedCourse
from ..test_utils import restrict_course


@ddt.ddt
@skip_unless_lms
class EmbargoMiddlewareAccessTests(UrlResetMixin, ModuleStoreTestCase):
    """Tests of embargo middleware country access rules.

    There are detailed unit tests for the rule logic in
    `test_api.py`; here, we're mainly testing the integration
    with middleware

    """
    USERNAME = 'fred'
    PASSWORD = 'secret'

    URLCONF_MODULES = ['openedx.core.djangoapps.embargo']

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):
        super(EmbargoMiddlewareAccessTests, self).setUp()
        self.user = UserFactory(username=self.USERNAME, password=self.PASSWORD)
        self.course = CourseFactory.create()
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

        self.courseware_url = reverse(
            'openedx.course_experience.course_home',
            kwargs={'course_id': six.text_type(self.course.id)}
        )
        self.non_courseware_url = reverse('dashboard')

        # Clear the cache to avoid interference between tests
        django_cache.clear()
        config_cache.clear()

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    @ddt.data(True, False)
    def test_blocked(self, disable_access_check):
        with restrict_course(self.course.id, access_point='courseware', disable_access_check=disable_access_check) as redirect_url:  # pylint: disable=line-too-long
            response = self.client.get(self.courseware_url)
            if disable_access_check:
                self.assertEqual(response.status_code, 200)
            else:
                self.assertRedirects(response, redirect_url)

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_allowed(self):
        # Add the course to the list of restricted courses
        # but don't create any access rules
        RestrictedCourse.objects.create(course_key=self.course.id)

        # Expect that we can access courseware
        response = self.client.get(self.courseware_url)
        self.assertEqual(response.status_code, 200)

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_non_courseware_url(self):
        with restrict_course(self.course.id):
            response = self.client.get(self.non_courseware_url)
            self.assertEqual(response.status_code, 200)

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    @ddt.data(
        # request_ip, blacklist, whitelist, is_enabled, allow_access
        (u'173.194.123.35', ['173.194.123.35'], [], True, False),
        (u'173.194.123.35', ['173.194.0.0/16'], [], True, False),
        (u'173.194.123.35', ['127.0.0.0/32', '173.194.0.0/16'], [], True, False),
        (u'173.195.10.20', ['173.194.0.0/16'], [], True, True),
        (u'173.194.123.35', ['173.194.0.0/16'], ['173.194.0.0/16'], True, False),
        (u'173.194.123.35', [], ['173.194.0.0/16'], True, True),
        (u'192.178.2.3', [], ['173.194.0.0/16'], True, True),
        (u'173.194.123.35', ['173.194.123.35'], [], False, True),
    )
    @ddt.unpack
    def test_ip_access_rules(self, request_ip, blacklist, whitelist, is_enabled, allow_access):
        # Ensure that IP blocking works for anonymous users
        self.client.logout()

        # Set up the IP rules
        IPFilter.objects.create(
            blacklist=", ".join(blacklist),
            whitelist=", ".join(whitelist),
            enabled=is_enabled
        )

        # Check that access is enforced
        response = self.client.get(
            "/",
            HTTP_X_FORWARDED_FOR=request_ip,
            REMOTE_ADDR=request_ip
        )

        if allow_access:
            self.assertEqual(response.status_code, 200)
        else:
            redirect_url = reverse(
                'embargo:blocked_message',
                kwargs={
                    'access_point': 'courseware',
                    'message_key': 'embargo'
                }
            )
            self.assertRedirects(response, redirect_url)

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    @ddt.data(
        ('courseware', 'default'),
        ('courseware', 'embargo'),
        ('enrollment', 'default'),
        ('enrollment', 'embargo')
    )
    @ddt.unpack
    def test_always_allow_access_to_embargo_messages(self, access_point, msg_key):
        # Blacklist an IP address
        IPFilter.objects.create(
            blacklist="192.168.10.20",
            enabled=True
        )

        url = reverse(
            'embargo:blocked_message',
            kwargs={
                'access_point': access_point,
                'message_key': msg_key
            }
        )
        response = self.client.get(
            url,
            HTTP_X_FORWARDED_FOR="192.168.10.20",
            REMOTE_ADDR="192.168.10.20"
        )
        self.assertEqual(response.status_code, 200)

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_whitelist_ip_skips_country_access_checks(self):
        # Whitelist an IP address
        IPFilter.objects.create(
            whitelist=u"192.168.10.20",
            enabled=True
        )

        # Set up country access rules so the user would
        # be restricted from the course.
        with restrict_course(self.course.id):
            # Make a request from the whitelisted IP address
            response = self.client.get(
                self.courseware_url,
                HTTP_X_FORWARDED_FOR=u"192.168.10.20",
                REMOTE_ADDR=u"192.168.10.20"
            )

        # Expect that we were still able to access the page,
        # even though we would have been blocked by country
        # access rules.
        self.assertEqual(response.status_code, 200)
