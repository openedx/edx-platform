# pylint: disable=missing-docstring
from __future__ import unicode_literals

import six
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from student.cookies import get_user_info_cookie_data
from student.models import CourseEnrollment
from student.tests.factories import UserFactory


class CookieTests(SharedModuleStoreTestCase):
    @classmethod
    def setUpClass(cls):
        super(CookieTests, cls).setUpClass()
        cls.course = CourseFactory()

    def setUp(self):
        super(CookieTests, self).setUp()
        self.user = UserFactory.create()

    def _get_expected_header_urls(self, request):
        expected_header_urls = {
            'logout': reverse('logout'),
        }

        # Studio (CMS) does not have the URLs below
        if settings.ROOT_URLCONF == 'lms.urls':
            expected_header_urls.update({
                'account_settings': reverse('account_settings'),
                'learner_profile': reverse('learner_profile', kwargs={'username': self.user.username}),
            })

        # Convert relative URL paths to absolute URIs
        for url_name, url_path in six.iteritems(expected_header_urls):
            expected_header_urls[url_name] = request.build_absolute_uri(url_path)

        return expected_header_urls

    def test_get_user_info_cookie_data(self):
        request = RequestFactory().get('/')
        request.user = self.user

        actual = get_user_info_cookie_data(request)

        expected = {
            'version': settings.EDXMKTG_USER_INFO_COOKIE_VERSION,
            'username': self.user.username,
            'header_urls': self._get_expected_header_urls(request),
            'enrollmentStatusHash': CourseEnrollment.generate_enrollment_status_hash(self.user)
        }

        self.assertDictEqual(actual, expected)
