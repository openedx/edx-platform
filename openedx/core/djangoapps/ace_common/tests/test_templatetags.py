# pylint: disable=missing-docstring,no-member
import uuid

from django.http import HttpRequest
from django.template import VariableDoesNotExist
from django.test import override_settings
from mock import patch

from edx_ace import Message, Recipient
from openedx.core.djangoapps.ace_common.templatetags.ace import (
    ensure_url_is_absolute,
    with_link_tracking,
    google_analytics_tracking_pixel,
    _get_google_analytics_tracking_url
)
from openedx.core.djangoapps.ace_common.tests.mixins import QueryStringAssertionMixin
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from student.tests.factories import UserFactory


@skip_unless_lms
class TestAbsoluteUrl(CacheIsolationTestCase):
    def setUp(self):
        self.site = SiteFactory.create()
        self.site.domain = 'example.com'
        super(TestAbsoluteUrl, self).setUp()

    def test_absolute_url(self):
        absolute = ensure_url_is_absolute(self.site, '/foo/bar')
        self.assertEqual(absolute, 'https://example.com/foo/bar')

    def test_absolute_url_domain_lstrip(self):
        self.site.domain = 'example.com/'
        absolute = ensure_url_is_absolute(self.site, 'foo/bar')
        self.assertEqual(absolute, 'https://example.com/foo/bar')

    def test_absolute_url_already_absolute(self):
        absolute = ensure_url_is_absolute(self.site, 'https://some-cdn.com/foo/bar')
        self.assertEqual(absolute, 'https://some-cdn.com/foo/bar')


class EmailTemplateTagMixin(object):

    def setUp(self):
        patcher = patch('openedx.core.djangoapps.ace_common.templatetags.ace.get_current_request')
        self.mock_get_current_request = patcher.start()
        self.addCleanup(patcher.stop)

        self.fake_request = HttpRequest()
        self.fake_request.user = UserFactory.create()
        self.fake_request.site = SiteFactory.create()
        self.fake_request.site.domain = 'example.com'
        self.mock_get_current_request.return_value = self.fake_request

        self.message = Message(
            app_label='test_app_label',
            name='test_name',
            recipient=Recipient(username='test_user'),
            context={},
            send_uuid=uuid.uuid4(),
        )
        self.context = {
            'message': self.message
        }


@skip_unless_lms
class TestLinkTrackingTag(QueryStringAssertionMixin, EmailTemplateTagMixin, CacheIsolationTestCase):

    def test_default(self):
        result_url = str(with_link_tracking(self.context, 'http://example.com/foo'))
        self.assert_url_components_equal(
            result_url,
            scheme='http',
            netloc='example.com',
            path='/foo',
            query='utm_source=test_app_label&utm_campaign=test_name&utm_medium=email&utm_content={uuid}'.format(
                uuid=self.message.uuid
            )
        )

    def test_missing_request(self):
        self.mock_get_current_request.return_value = None

        with self.assertRaises(VariableDoesNotExist):
            with_link_tracking(self.context, 'http://example.com/foo')

    def test_missing_message(self):
        del self.context['message']

        with self.assertRaises(VariableDoesNotExist):
            with_link_tracking(self.context, 'http://example.com/foo')

    def test_course_id(self):
        self.context['course_ids'] = ['foo/bar/baz']
        result_url = str(with_link_tracking(self.context, 'http://example.com/foo'))
        self.assert_query_string_parameters_equal(
            result_url,
            utm_term='foo/bar/baz',
        )

    def test_multiple_course_ids(self):
        self.context['course_ids'] = ['foo/bar/baz', 'course-v1:FooX+bar+baz']
        result_url = str(with_link_tracking(self.context, 'http://example.com/foo'))
        self.assert_query_string_parameters_equal(
            result_url,
            utm_term='foo/bar/baz',
        )

    def test_relative_url(self):
        result_url = str(with_link_tracking(self.context, '/foobar'))
        self.assert_url_components_equal(
            result_url,
            scheme='https',
            netloc='example.com',
            path='/foobar'
        )


@skip_unless_lms
@override_settings(GOOGLE_ANALYTICS_TRACKING_ID='UA-123456-1')
class TestGoogleAnalyticsPixelTag(QueryStringAssertionMixin, EmailTemplateTagMixin, CacheIsolationTestCase):

    def test_default(self):
        result_url = _get_google_analytics_tracking_url(self.context)
        self.assert_query_string_parameters_equal(
            result_url,
            uid=self.fake_request.user.id,
            cs=self.message.app_label,
            cn=self.message.name,
            cc=self.message.uuid,
            dp='/email/test_app_label/test_name/{send_uuid}/{uuid}'.format(
                send_uuid=self.message.send_uuid,
                uuid=self.message.uuid,
            )
        )

    def test_missing_request(self):
        self.mock_get_current_request.return_value = None

        with self.assertRaises(VariableDoesNotExist):
            google_analytics_tracking_pixel(self.context)

    def test_missing_message(self):
        del self.context['message']

        with self.assertRaises(VariableDoesNotExist):
            google_analytics_tracking_pixel(self.context)

    def test_course_id(self):
        self.context['course_ids'] = ['foo/bar/baz']
        result_url = _get_google_analytics_tracking_url(self.context)
        self.assert_query_string_parameters_equal(
            result_url,
            el='foo/bar/baz',
        )

    def test_multiple_course_ids(self):
        self.context['course_ids'] = ['foo/bar/baz', 'course-v1:FooX+bar+baz']
        result_url = _get_google_analytics_tracking_url(self.context)
        self.assert_query_string_parameters_equal(
            result_url,
            el='foo/bar/baz',
        )

    def test_html_emitted(self):
        result_html = google_analytics_tracking_pixel(self.context)
        self.assertIn('<img src', result_html)

    @override_settings(GOOGLE_ANALYTICS_TRACKING_ID=None)
    def test_no_html_emitted_if_not_enabled(self):
        result_html = google_analytics_tracking_pixel(self.context)
        self.assertEqual('', result_html)
