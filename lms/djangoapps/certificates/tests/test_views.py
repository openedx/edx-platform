"""Tests for certificates views. """


import datetime
import json
from uuid import uuid4

import ddt
import six
from django.conf import settings
from django.core.cache import cache
from django.test.client import Client
from django.test.utils import override_settings
from django.urls import reverse
from opaque_keys.edx.locator import CourseLocator
from six.moves import range

from lms.djangoapps.certificates.api import get_certificate_url
from lms.djangoapps.certificates.models import (
    CertificateHtmlViewConfiguration,
    ExampleCertificate,
    ExampleCertificateSet,
    GeneratedCertificate
)
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

FEATURES_WITH_CERTS_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_ENABLED['CERTIFICATES_HTML_VIEW'] = True

FEATURES_WITH_CERTS_DISABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_DISABLED['CERTIFICATES_HTML_VIEW'] = False

FEATURES_WITH_CUSTOM_CERTS_ENABLED = {
    "CUSTOM_CERTIFICATE_TEMPLATES_ENABLED": True
}
FEATURES_WITH_CUSTOM_CERTS_ENABLED.update(FEATURES_WITH_CERTS_ENABLED)


@ddt.ddt
class UpdateExampleCertificateViewTest(CacheIsolationTestCase):
    """Tests for the XQueue callback that updates example certificates. """

    COURSE_KEY = CourseLocator(org='test', course='test', run='test')

    DESCRIPTION = 'test'
    TEMPLATE = 'test.pdf'
    DOWNLOAD_URL = 'http://www.example.com'
    ERROR_REASON = 'Kaboom!'

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(UpdateExampleCertificateViewTest, self).setUp()
        self.cert_set = ExampleCertificateSet.objects.create(course_key=self.COURSE_KEY)
        self.cert = ExampleCertificate.objects.create(
            example_cert_set=self.cert_set,
            description=self.DESCRIPTION,
            template=self.TEMPLATE,
        )
        self.url = reverse('update_example_certificate')

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
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['return_code'], 0)


class CertificatesViewsSiteTests(ModuleStoreTestCase):
    """
    Tests for the certificates web/html views
    """
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

    def setUp(self):
        super(CertificatesViewsSiteTests, self).setUp()
        self.client = Client()
        self.course = CourseFactory.create(
            org='testorg',
            number='run1',
            display_name='refundable course',
            certificate_available_date=datetime.datetime.today() - datetime.timedelta(days=1)
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
            download_uuid=uuid4().hex,
            grade="0.95",
            key='the_key',
            distinction=True,
            status='downloadable',
            mode='honor',
            name=self.user.profile.name,
            verify_uuid=uuid4().hex
        )
        self._setup_configuration()

    def _setup_configuration(self, enabled=True):
        """
        This will create a certificate html configuration
        """
        config = CertificateHtmlViewConfiguration(enabled=enabled, configuration=self.test_configuration_string)
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
            } for i in range(signatory_count)

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
            } for i in range(count)
        ]

        self.course.certificates = {'certificates': certificates}
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    @with_site_configuration(configuration={'platform_name': 'My Platform Site'})
    def test_html_view_for_site(self):
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        self._add_course_certificates(count=1, signatory_count=2)
        response = self.client.get(test_url)
        self.assertContains(
            response,
            'awarded this My Platform Site Honor Code Certificate of Completion',
        )
        self.assertContains(
            response,
            'My Platform Site offers interactive online classes and MOOCs.'
        )
        self.assertContains(response, 'About My Platform Site')

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_html_view_site_configuration_missing(self):
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        self._add_course_certificates(count=1, signatory_count=2)
        response = self.client.get(test_url)
        self.assertContains(response, 'edX')
        self.assertNotContains(response, 'My Platform Site')
        self.assertNotContains(
            response,
            'This should not survive being overwritten by static content',
        )
