"""Tests for certificates views. """

import json
import ddt
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

from opaque_keys.edx.locator import CourseLocator
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from certificates.models import ExampleCertificateSet, ExampleCertificate, GeneratedCertificate
from certificates.tests.factories import CertificateHtmlViewConfigurationFactory

FEATURES_WITH_CERTS_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_ENABLED['CERTIFICATES_HTML_VIEW'] = True

FEATURES_WITH_CERTS_DISABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_DISABLED['CERTIFICATES_HTML_VIEW'] = False


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


class CertificatesViewsTests(ModuleStoreTestCase):
    """
    Tests for the manual refund page
    """
    def setUp(self):
        super(CertificatesViewsTests, self).setUp()
        self.client = Client()
        self.course = CourseFactory.create(
            org='testorg', number='run1', display_name='refundable course'
        )
        self.course_id = self.course.location.course_key
        self.user = UserFactory.create(
            email='joe_user@edx.org',
            username='joeuser',
            password='foo'
        )
        self.user.profile.name = "Joe User"
        self.user.profile.save()
        self.client.login(username=self.user.username, password='foo')

        self.cert = GeneratedCertificate.objects.create(
            user=self.user,
            course_id=self.course_id,
            verify_uuid=uuid4(),
            download_uuid=uuid4(),
            grade="0.95",
            key='the_key',
            distinction=True,
            status='generated',
            mode='honor',
            name=self.user.profile.name,
        )
        CertificateHtmlViewConfigurationFactory.create()

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_valid_certificate(self):
        test_url = '/certificates/html?course={}'.format(unicode(self.course.id))
        response = self.client.get(test_url)
        self.assertIn(str(self.cert.verify_uuid), response.content)

        # Hit any "verified" mode-specific branches
        self.cert.mode = 'verified'
        self.cert.save()
        test_url = '/certificates/html?course={}'.format(unicode(self.course.id))
        response = self.client.get(test_url)
        self.assertIn(str(self.cert.verify_uuid), response.content)

        # Hit any 'xseries' mode-specific branches
        self.cert.mode = 'xseries'
        self.cert.save()
        test_url = '/certificates/html?course={}'.format(unicode(self.course.id))
        response = self.client.get(test_url)
        self.assertIn(str(self.cert.verify_uuid), response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_DISABLED)
    def test_render_html_view_invalid_feature_flag(self):
        test_url = '/certificates/html?course={}'.format(unicode(self.course.id))
        response = self.client.get(test_url)
        self.assertIn('invalid', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_missing_course_id(self):
        test_url = '/certificates/html'
        response = self.client.get(test_url)
        self.assertIn('invalid', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_course_id(self):
        test_url = '/certificates/html?course=az-23423-4vs'
        response = self.client.get(test_url)
        self.assertIn('invalid', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_course(self):
        test_url = '/certificates/html?course=missing/course/key'
        response = self.client.get(test_url)
        self.assertIn('invalid', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_certificate(self):
        self.cert.delete()
        self.assertEqual(len(GeneratedCertificate.objects.all()), 0)
        test_url = '/certificates/html?course={}'.format(unicode(self.course.id))
        response = self.client.get(test_url)
        self.assertIn('invalid', response.content)
