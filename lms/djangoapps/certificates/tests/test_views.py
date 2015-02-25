"""Tests for certificates views. """

import json
import ddt

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.cache import cache

from opaque_keys.edx.locator import CourseLocator

from certificates.models import ExampleCertificateSet, ExampleCertificate


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
