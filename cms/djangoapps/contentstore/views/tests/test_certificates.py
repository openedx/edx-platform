#-*- coding: utf-8 -*-

"""
Group Configuration Tests.
"""
import json
import mock

from contentstore.utils import reverse_course_url
from contentstore.views.certificates import CERTIFICATE_SCHEMA_VERSION
from contentstore.tests.utils import CourseTestCase
from student.models import CourseEnrollment
from contentstore.views.certificates import CertificateManager

CERTIFICATE_JSON = {
    u'name': u'Test certificate',
    u'description': u'Test description',
    u'version': CERTIFICATE_SCHEMA_VERSION
}

CERTIFICATE_JSON_WITH_SIGNATORIES = {
    u'name': u'Test certificate',
    u'description': u'Test description',
    u'version': CERTIFICATE_SCHEMA_VERSION,
    u'signatories': [{"name": "Bob Smith", "title": "The DEAN."}]
}


# pylint: disable=no-member
class HelperMethods(object):
    """
    Mixin that provides useful methods for certificate configuration tests.
    """
    def _add_course_certificates(self, count=1, signatory_count=0):
        """
        Create certificate for the course.
        """
        signatories = [
            {
                'name': 'Name ' + str(i),
                'title': 'Title ' + str(i),
                'id': i
            } for i in xrange(0, signatory_count)

        ]

        certificates = [
            {
                'id': i,
                'name': 'Name ' + str(i),
                'description': 'Description ' + str(i),
                'signatories': signatories,
                'version': CERTIFICATE_SCHEMA_VERSION
            } for i in xrange(0, count)
        ]

        self.course.certificates = {'certificates': certificates}
        self.save_course()


# pylint: disable=no-member
class CertificatesBaseTestCase(object):
    """
    Mixin with base test cases for the certificates.
    """

    def _remove_ids(self, content):
        """
        Remove ids from the response. We cannot predict IDs, because they're
        generated randomly.
        We use this method to clean up response when creating new certificate.
        """
        certificate_id = content.pop("id")
        return certificate_id

    def test_required_fields_are_absent(self):
        """
        Test required fields are absent.
        """
        bad_jsons = [
            # must have name of the certificate
            {
                u'description': 'Test description',
                u'version': CERTIFICATE_SCHEMA_VERSION
            },

            # an empty json
            {},
        ]

        for bad_json in bad_jsons:
            response = self.client.post(
                self._url(),
                data=json.dumps(bad_json),
                content_type="application/json",
                HTTP_ACCEPT="application/json",
                HTTP_X_REQUESTED_WITH="XMLHttpRequest"
            )

            self.assertEqual(response.status_code, 400)
            self.assertNotIn("Location", response)
            content = json.loads(response.content)
            self.assertIn("error", content)

    def test_invalid_json(self):
        """
        Test invalid json handling.
        """
        # Invalid JSON.
        invalid_json = "{u'name': 'Test Name', u'description': 'Test description'," \
                       " u'version': " + str(CERTIFICATE_SCHEMA_VERSION) + ", []}"

        response = self.client.post(
            self._url(),
            data=invalid_json,
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("Location", response)
        content = json.loads(response.content)
        self.assertIn("error", content)

    def test_certificate_data_validation(self):
        #Test certificate schema version
        json_data_1 = {
            u'version': 100,
            u'name': u'Test certificate',
            u'description': u'Test description'
        }

        with self.assertRaises(Exception) as context:
            CertificateManager.validate(json_data_1)

        self.assertTrue("Unsupported certificate schema version: 100.  Expected version: 1." in context.exception)

        #Test certificate name is missing
        json_data_2 = {
            u'version': CERTIFICATE_SCHEMA_VERSION,
            u'description': u'Test description'
        }

        with self.assertRaises(Exception) as context:
            CertificateManager.validate(json_data_2)

        self.assertTrue('must have name of the certificate' in context.exception)


# pylint: disable=no-member
class CertificatesListHandlerTestCase(CourseTestCase, CertificatesBaseTestCase, HelperMethods):
    """
    Test cases for certificates_list_handler.
    """
    def setUp(self):
        """
        Set up CertificatesListHandlerTestCase.
        """
        super(CertificatesListHandlerTestCase, self).setUp()

    def _url(self):
        """
        Return url for the handler.
        """
        return reverse_course_url('certificates.certificates_list_handler', self.course.id)

    def test_can_create_certificate(self):
        """
        Test that you can create a certificate.
        """
        expected = {
            u'version': CERTIFICATE_SCHEMA_VERSION,
            u'name': u'Test certificate',
            u'description': u'Test description',
            u'signatories': []
        }
        response = self.client.ajax_post(
            self._url(),
            data=CERTIFICATE_JSON
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("Location", response)
        content = json.loads(response.content)
        self._remove_ids(content)  # pylint: disable=unused-variable
        self.assertEqual(content, expected)

    @mock.patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_certificate_info_in_response(self):
        """
        Test that certificate has been created and rendered properly.
        """
        response = self.client.ajax_post(
            self._url(),
            data=CERTIFICATE_JSON_WITH_SIGNATORIES
        )

        self.assertEqual(response.status_code, 201)

        # in html response
        result = self.client.get_html(self._url())
        print self._url()
        self.assertIn('Test certificate', result.content)
        self.assertIn('Test description', result.content)

        # in JSON response
        response = self.client.get_json(self._url())
        data = json.loads(response.content)
        self.assertEquals(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test certificate')
        self.assertEqual(data[0]['description'], 'Test description')
        self.assertEqual(data[0]['version'], CERTIFICATE_SCHEMA_VERSION)

    def test_unsupported_http_accept_header(self):
        """
        Test if not allowed header present in request.
        """
        response = self.client.get(
            self._url(),
            HTTP_ACCEPT="text/plain",
        )
        self.assertEqual(response.status_code, 406)

    def test_certificate_unsupported_method(self):
        """
        Unit Test: test_certificate_unsupported_method
        """
        resp = self.client.put(self._url())
        self.assertEqual(resp.status_code, 405)

    def test_not_permitted(self):
        """
        Test that when user has not read access to course then permission denied exception should raised.
        """
        test_user_client, test_user = self.create_non_staff_authed_user_client()
        CourseEnrollment.enroll(test_user, self.course.id)
        response = test_user_client.ajax_post(
            self._url(),
            data=CERTIFICATE_JSON
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.content)

    def test_assign_unique_identifier_to_certificates(self):
        """
        Test certificates have unique ids
        """
        self._add_course_certificates(count=2)
        json_data = {
            u'version': CERTIFICATE_SCHEMA_VERSION,
            u'name': u'New test certificate',
            u'description': u'New test description',
            u'signatories': []
        }

        response = self.client.post(
            self._url(),
            data=json.dumps(json_data),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        new_certificate = json.loads(response.content)
        for prev_certificate in self.course.certificates['certificates']:
            self.assertNotEqual(new_certificate.get('id'), prev_certificate.get('id'))


class CertificatesDetailHandlerTestCase(CourseTestCase, CertificatesBaseTestCase, HelperMethods):
    """
    Test cases for CertificatesDetailHandlerTestCase.
    """

    _id = 0

    def _url(self, cid=-1):
        """
        Return url for the handler.
        """
        cid = cid if cid > 0 else self._id
        return reverse_course_url(
            'certificates.certificates_detail_handler',
            self.course.id,
            kwargs={'certificate_id': cid},
        )

    def test_can_create_new_certificate_if_it_does_not_exist(self):
        """
        PUT/POST new certificate.
        """
        expected = {
            u'id': 666,
            u'version': CERTIFICATE_SCHEMA_VERSION,
            u'name': u'Test certificate',
            u'description': u'Test description',
            u'signatories': []
        }

        response = self.client.put(
            self._url(cid=666),
            data=json.dumps(expected),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        content = json.loads(response.content)
        self.assertEqual(content, expected)

    def test_can_edit_certificate(self):
        """
        Edit certificate, check its id and modified fields.
        """
        self._add_course_certificates(count=2)

        expected = {
            u'id': 1,
            u'version': CERTIFICATE_SCHEMA_VERSION,
            u'name': u'New test certificate',
            u'description': u'New test description',
            u'signatories': []
        }

        response = self.client.put(
            self._url(cid=1),
            data=json.dumps(expected),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        content = json.loads(response.content)
        self.assertEqual(content, expected)
        self.reload_course()

        # Verify that certificate is properly updated in the course.
        course_certificates = self.course.certificates['certificates']
        self.assertEqual(len(course_certificates), 2)
        self.assertEqual(course_certificates[1].get('name'), u'New test certificate')
        self.assertEqual(course_certificates[1].get('description'), 'New test description')

    def test_can_delete_certificate(self):
        """
        Delete certificate
        """
        self._add_course_certificates(count=2)
        response = self.client.delete(
            self._url(cid=1),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 204)
        self.reload_course()
        # Verify that certificates are properly updated in the course.
        certificates = self.course.certificates['certificates']
        self.assertEqual(len(certificates), 1)
        self.assertEqual(certificates[0].get('name'), 'Name 0')
        self.assertEqual(certificates[0].get('description'), 'Description 0')

    def test_delete_non_existing_certificate(self):
        """
        Try to delete a non existing certificate. It should return status code 404 Not found.
        """
        self._add_course_certificates(count=2)
        response = self.client.delete(
            self._url(cid=100),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 404)

    def test_can_delete_signatory(self):
        """
        Delete an existing certificate signatory
        """
        self._add_course_certificates(count=2, signatory_count=3)
        test_url = '{}/signatories/1'.format(self._url(cid=1))
        response = self.client.delete(
            test_url,
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 204)
        self.reload_course()
        # Verify that certificates are properly updated in the course.
        certificates = self.course.certificates['certificates']
        self.assertEqual(len(certificates[1].get("signatories")), 2)

    def test_delete_signatory_non_existing_certificate(self):
        """
        Try to delete a non existing certificate signatory. It should return status code 404 Not found.
        """
        self._add_course_certificates(count=2)
        test_url = '{}/signatories/1'.format(self._url(cid=100))
        response = self.client.delete(
            test_url,
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 404)
