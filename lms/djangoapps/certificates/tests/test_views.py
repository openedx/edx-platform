"""Tests for certificates views. """

import json
import ddt
from uuid import uuid4
from nose.plugins.attrib import attr
from mock import patch

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

from opaque_keys.edx.locator import CourseLocator
from openedx.core.lib.tests.assertions.events import assert_event_matches
from student.tests.factories import UserFactory
from track.tests import EventTrackingTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from util.testing import UrlResetMixin

from certificates.api import get_certificate_url
from certificates.models import (
    ExampleCertificateSet,
    ExampleCertificate,
    GeneratedCertificate,
    CertificateHtmlViewConfiguration,
)

from certificates.tests.factories import (
    BadgeAssertionFactory,
)

FEATURES_WITH_CERTS_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_ENABLED['CERTIFICATES_HTML_VIEW'] = True

FEATURES_WITH_CERTS_DISABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_DISABLED['CERTIFICATES_HTML_VIEW'] = False

FEATURES_WITH_CUSTOM_CERTS_ENABLED = {
    "CUSTOM_CERTIFICATE_TEMPLATES_ENABLED": True
}
FEATURES_WITH_CUSTOM_CERTS_ENABLED.update(FEATURES_WITH_CERTS_ENABLED)


@attr('shard_1')
@ddt.ddt
class UpdateExampleCertificateViewTest(TestCase):
    """Tests for the XQueue callback that updates example certificates. """

    COURSE_KEY = CourseLocator(org='test', course='test', run='test')

    DESCRIPTION = 'test'
    TEMPLATE = 'test.pdf'
    DOWNLOAD_URL = 'http://www.example.com'
    ERROR_REASON = 'Kaboom!'

    def setUp(self):
        super(UpdateExampleCertificateViewTest, self).setUp()
        self.cert_set = ExampleCertificateSet.objects.create(course_key=self.COURSE_KEY)
        self.cert = ExampleCertificate.objects.create(
            example_cert_set=self.cert_set,
            description=self.DESCRIPTION,
            template=self.TEMPLATE,
        )
        self.url = reverse('certificates.views.update_example_certificate')

        # Since rate limit counts are cached, we need to clear
        # this before each test.
        cache.clear()

    def test_update_example_certificate_success(self):
        response = self._post_to_view(self.cert, download_url=self.DOWNLOAD_URL)
        self._assert_response(response)

        self.cert = ExampleCertificate.objects.get()
        self.assertEqual(self.cert.status, ExampleCertificate.STATUS_SUCCESS)
        self.assertEqual(self.cert.download_url, self.DOWNLOAD_URL)

    def test_update_example_certificate_invalid_key(self):
        payload = {
            'xqueue_header': json.dumps({
                'lms_key': 'invalid'
            }),
            'xqueue_body': json.dumps({
                'username': self.cert.uuid,
                'url': self.DOWNLOAD_URL
            })
        }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 404)

    def test_update_example_certificate_error(self):
        response = self._post_to_view(self.cert, error_reason=self.ERROR_REASON)
        self._assert_response(response)

        self.cert = ExampleCertificate.objects.get()
        self.assertEqual(self.cert.status, ExampleCertificate.STATUS_ERROR)
        self.assertEqual(self.cert.error_reason, self.ERROR_REASON)

    @ddt.data('xqueue_header', 'xqueue_body')
    def test_update_example_certificate_invalid_params(self, missing_param):
        payload = {
            'xqueue_header': json.dumps({
                'lms_key': self.cert.access_key
            }),
            'xqueue_body': json.dumps({
                'username': self.cert.uuid,
                'url': self.DOWNLOAD_URL
            })
        }
        del payload[missing_param]

        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 400)

    def test_update_example_certificate_missing_download_url(self):
        payload = {
            'xqueue_header': json.dumps({
                'lms_key': self.cert.access_key
            }),
            'xqueue_body': json.dumps({
                'username': self.cert.uuid
            })
        }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 400)

    def test_update_example_cetificate_non_json_param(self):
        payload = {
            'xqueue_header': '{/invalid',
            'xqueue_body': '{/invalid'
        }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, 400)

    def test_unsupported_http_method(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_bad_request_rate_limiting(self):
        payload = {
            'xqueue_header': json.dumps({
                'lms_key': 'invalid'
            }),
            'xqueue_body': json.dumps({
                'username': self.cert.uuid,
                'url': self.DOWNLOAD_URL
            })
        }

        # Exceed the rate limit for invalid requests
        # (simulate a DDOS with invalid keys)
        for _ in range(100):
            response = self.client.post(self.url, data=payload)
            if response.status_code == 403:
                break

        # The final status code should indicate that the rate
        # limit was exceeded.
        self.assertEqual(response.status_code, 403)

    def _post_to_view(self, cert, download_url=None, error_reason=None):
        """Simulate a callback from the XQueue to the example certificate end-point. """
        header = {'lms_key': cert.access_key}
        body = {'username': cert.uuid}

        if download_url is not None:
            body['url'] = download_url

        if error_reason is not None:
            body['error'] = 'error'
            body['error_reason'] = self.ERROR_REASON

        payload = {
            'xqueue_header': json.dumps(header),
            'xqueue_body': json.dumps(body)
        }
        return self.client.post(self.url, data=payload)

    def _assert_response(self, response):
        """Check the response from the callback end-point. """
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['return_code'], 0)


@attr('shard_1')
class MicrositeCertificatesViewsTests(ModuleStoreTestCase):
    """
    Tests for the microsite certificates web/html views
    """
    def setUp(self):
        super(MicrositeCertificatesViewsTests, self).setUp()
        self.client = Client()
        self.course = CourseFactory.create(
            org='testorg', number='run1', display_name='refundable course'
        )
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)
        self.course_id = self.course.location.course_key
        self.user = UserFactory.create(
            email='joe_user@edx.org',
            username='joeuser',
            password='foo'
        )
        self.user.profile.name = "Joe User"
        self.user.profile.save()
        self.client.login(username=self.user.username, password='foo')
        self.cert = GeneratedCertificate.eligible_certificates.create(
            user=self.user,
            course_id=self.course_id,
            download_uuid=uuid4(),
            grade="0.95",
            key='the_key',
            distinction=True,
            status='downloadable',
            mode='honor',
            name=self.user.profile.name,
        )

    def _certificate_html_view_configuration(self, configuration_string, enabled=True):
        """
        This will create a certificate html configuration
        """
        config = CertificateHtmlViewConfiguration(enabled=enabled, configuration=configuration_string)
        config.save()
        return config

    def _add_course_certificates(self, count=1, signatory_count=0, is_active=True):
        """
        Create certificate for the course.
        """
        signatories = [
            {
                'name': 'Signatory_Name ' + str(i),
                'title': 'Signatory_Title ' + str(i),
                'organization': 'Signatory_Organization ' + str(i),
                'signature_image_path': '/static/certificates/images/demo-sig{}.png'.format(i),
                'id': i,
            } for i in xrange(signatory_count)

        ]

        certificates = [
            {
                'id': i,
                'name': 'Name ' + str(i),
                'description': 'Description ' + str(i),
                'course_title': 'course_title_' + str(i),
                'signatories': signatories,
                'version': 1,
                'is_active': is_active
            } for i in xrange(count)
        ]

        self.course.certificates = {'certificates': certificates}
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_html_view_for_microsite(self):
        test_configuration_string = """{
            "default": {
                "accomplishment_class_append": "accomplishment-certificate",
                "platform_name": "edX",
                "company_about_url": "http://www.edx.org/about-us",
                "company_privacy_url": "http://www.edx.org/edx-privacy-policy",
                "company_tos_url": "http://www.edx.org/edx-terms-service",
                "company_verified_certificate_url": "http://www.edx.org/verified-certificate",
                "document_stylesheet_url_application": "/static/certificates/sass/main-ltr.css",
                "logo_src": "/static/certificates/images/logo-edx.svg",
                "logo_url": "http://www.edx.org"
            },
            "microsites": {
                "testmicrosite": {
                    "accomplishment_class_append": "accomplishment-certificate",
                    "platform_name": "platform_microsite",
                    "company_about_url": "http://www.microsite.org/about-us",
                    "company_privacy_url": "http://www.microsite.org/edx-privacy-policy",
                    "company_tos_url": "http://www.microsite.org/microsite-terms-service",
                    "company_verified_certificate_url": "http://www.microsite.org/verified-certificate",
                    "document_stylesheet_url_application": "/static/certificates/sass/main-ltr.css",
                    "logo_src": "/static/certificates/images/logo-microsite.svg",
                    "logo_url": "http://www.microsite.org",
                    "company_about_description": "This is special microsite aware company_about_description content",
                    "company_about_title": "Microsite title"
                }
            },
            "honor": {
                "certificate_type": "Honor Code"
            }
        }"""

        config = self._certificate_html_view_configuration(configuration_string=test_configuration_string)
        self.assertEquals(config.configuration, test_configuration_string)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        self._add_course_certificates(count=1, signatory_count=2)
        response = self.client.get(test_url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertIn('platform_microsite', response.content)
        self.assertIn('http://www.microsite.org', response.content)
        self.assertIn('This is special microsite aware company_about_description content', response.content)
        self.assertIn('Microsite title', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_html_view_microsite_configuration_missing(self):
        test_configuration_string = """{
            "default": {
                "accomplishment_class_append": "accomplishment-certificate",
                "platform_name": "edX",
                "company_about_url": "http://www.edx.org/about-us",
                "company_privacy_url": "http://www.edx.org/edx-privacy-policy",
                "company_tos_url": "http://www.edx.org/edx-terms-service",
                "company_verified_certificate_url": "http://www.edx.org/verified-certificate",
                "document_stylesheet_url_application": "/static/certificates/sass/main-ltr.css",
                "logo_src": "/static/certificates/images/logo-edx.svg",
                "logo_url": "http://www.edx.org",
                "company_about_description": "This should not survive being overwritten by static content"
            },
            "honor": {
                "certificate_type": "Honor Code"
            }
        }"""
        config = self._certificate_html_view_configuration(configuration_string=test_configuration_string)
        self.assertEquals(config.configuration, test_configuration_string)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        self._add_course_certificates(count=1, signatory_count=2)
        response = self.client.get(test_url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertIn('edX', response.content)
        self.assertNotIn('platform_microsite', response.content)
        self.assertNotIn('http://www.microsite.org', response.content)
        self.assertNotIn('This should not survive being overwritten by static content', response.content)


class TrackShareRedirectTest(UrlResetMixin, ModuleStoreTestCase, EventTrackingTestCase):
    """
    Verifies the badge image share event is sent out.
    """

    @patch.dict(settings.FEATURES, {"ENABLE_OPENBADGES": True})
    def setUp(self):
        super(TrackShareRedirectTest, self).setUp('certificates.urls')
        self.client = Client()
        self.course = CourseFactory.create(
            org='testorg', number='run1', display_name='trackable course'
        )
        self.assertion = BadgeAssertionFactory(
            user=self.user, course_id=self.course.id, data={
                'image': 'http://www.example.com/image.png',
                'json': {'id': 'http://www.example.com/assertion.json'},
                'issuer': 'http://www.example.com/issuer.json'
            },
        )

    def test_social_event_sent(self):
        test_url = '/certificates/badge_share_tracker/{}/social_network/{}/'.format(
            unicode(self.course.id),
            self.user.username,
        )
        self.recreate_tracker()
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://www.example.com/image.png')
        assert_event_matches(
            {
                'name': 'edx.badge.assertion.shared',
                'data': {
                    'course_id': 'testorg/run1/trackable_course',
                    'social_network': 'social_network',
                    # pylint: disable=no-member
                    'assertion_id': self.assertion.id,
                    'assertion_json_url': 'http://www.example.com/assertion.json',
                    'assertion_image_url': 'http://www.example.com/image.png',
                    'user_id': self.user.id,
                    'issuer': 'http://www.example.com/issuer.json',
                    'enrollment_mode': 'honor'
                },
            },
            self.get_event()
        )
