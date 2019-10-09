"""
Tests for logout for enterprise flow
"""
from __future__ import absolute_import

import ddt
import six.moves.urllib.parse as parse
from django.test.utils import override_settings
from django.urls import reverse


from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from openedx.features.enterprise_support.api import enterprise_enabled
from openedx.features.enterprise_support.tests import FEATURES_WITH_ENTERPRISE_ENABLED
from openedx.features.enterprise_support.tests.mixins.enterprise import EnterpriseServiceMockMixin
from util.url import reload_django_url_config


@ddt.ddt
@override_settings(FEATURES=FEATURES_WITH_ENTERPRISE_ENABLED)
@skip_unless_lms
class EnterpriseLogoutTests(EnterpriseServiceMockMixin, CacheIsolationTestCase):
    """ Tests for the enterprise logout functionality. """

    def setUp(self):
        reload_django_url_config()
        super(EnterpriseLogoutTests, self).setUp()

    @ddt.data(
        ('https%3A%2F%2Ftest.edx.org%2Fcourses', False),
        ('/courses/course-v1:ARTS+D1+2018_T/course/', False),
        ('invalid-url', False),
        ('/enterprise/c5dad9a7-741c-4841-868f-850aca3ff848/course/Microsoft+DAT206x/enroll/', True),
        ('%2Fenterprise%2Fc5dad9a7-741c-4841-868f-850aca3ff848%2Fcourse%2FMicrosoft%2BDAT206x%2Fenroll%2F', True),
    )
    @ddt.unpack
    def test_logout_enterprise_target(self, redirect_url, enterprise_target):
        url = '{logout_path}?redirect_url={redirect_url}'.format(
            logout_path=reverse('logout'),
            redirect_url=redirect_url
        )
        self.assertTrue(enterprise_enabled())
        quote_plus_url = parse.quote_plus(url)
        unquote_url = parse.unquote(quote_plus_url)

        quoted_url = parse.quote(unquote_url)
        unquote_plus_url = parse.unquote_plus(quoted_url)
        self.assertEqual(
            (quote_plus_url, unquote_url, quoted_url, unquote_plus_url),
            ('url1', 'url2', 'url3', 'url4'),
        )
        response = self.client.get(url, HTTP_HOST='testserver')
        expected = {
            'enterprise_target': enterprise_target,
        }
        self.assertDictContainsSubset(expected, response.context_data)
