#-*- coding: utf-8 -*-

"""
Certificates Tests.
"""
import itertools
import json
import mock
import ddt

from django.conf import settings
from django.test.utils import override_settings

from opaque_keys.edx.keys import AssetKey

from contentstore.utils import reverse_course_url
from contentstore.views.certificates import CERTIFICATE_SCHEMA_VERSION
from contentstore.tests.utils import CourseTestCase
from xmodule.contentstore.django import contentstore
from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError
from student.models import CourseEnrollment
from student.roles import CourseInstructorRole, CourseStaffRole
from student.tests.factories import UserFactory
from course_modes.tests.factories import CourseModeFactory
from contentstore.views.certificates import CertificateManager
from django.test.utils import override_settings
from contentstore.utils import get_lms_link_for_certificate_web_view
from util.testing import EventTestMixin, UrlResetMixin

FEATURES_WITH_CERTS_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_ENABLED['CERTIFICATES_HTML_VIEW'] = True

CERTIFICATE_JSON = {
    u'name': u'Test certificate',
    u'description': u'Test description',
    u'is_active': True,
    u'version': CERTIFICATE_SCHEMA_VERSION,
}

CERTIFICATE_JSON_WITH_SIGNATORIES = {
    u'name': u'Test certificate',
    u'description': u'Test description',
    u'version': CERTIFICATE_SCHEMA_VERSION,
    u'course_title': 'Course Title Override',
    u'is_active': True,
    u'signatories': [
        {
            "name": "Bob Smith",
            "title": "The DEAN.",
            "signature_image_path": "/c4x/test/CSS101/asset/Signature.png"
        }
    ]
}

C4X_SIGNATORY_PATH = '/c4x/test/CSS101/asset/Signature{}.png'
SIGNATORY_PATH = 'asset-v1:test+CSS101+SP2017+type@asset+block@Signature{}.png'


# pylint: disable=no-member
class HelperMethods(object):
    """
    Mixin that provides useful methods for certificate configuration tests.
    """
    def _create_fake_images(self, asset_keys):
        """
        Creates fake image files for a list of asset_keys.
        """
        for asset_key_string in asset_keys:
            asset_key = AssetKey.from_string(asset_key_string)
            content = StaticContent(
                asset_key, "Fake asset", "image/png", "data",
            )
            contentstore().save(content)

    def _add_course_certificates(self, count=1, signatory_count=0, is_active=False,
                                 asset_path_format=C4X_SIGNATORY_PATH):
        """
        Create certificate for the course.
        """
        signatories = [
            {
                'name': 'Name ' + str(i),
                'title': 'Title ' + str(i),
                'signature_image_path': asset_path_format.format(i),
                'id': i
            } for i in xrange(signatory_count)

        ]

        # create images for signatory signatures except the last signatory
        self._create_fake_images(signatory['signature_image_path'] for signatory in signatories[:-1])

        certificates = [
            {
                'id': i,
                'name': 'Name ' + str(i),
                'description': 'Description ' + str(i),
                'signatories': signatories,
                'version': CERTIFICATE_SCHEMA_VERSION,
                'is_active': is_active
            } for i in xrange(count)
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

        self.assertIn("Unsupported certificate schema version: 100.  Expected version: 1.", context.exception)

        #Test certificate name is missing
        json_data_2 = {
            u'version': CERTIFICATE_SCHEMA_VERSION,
            u'description': u'Test description'
        }

        with self.assertRaises(Exception) as context:
            CertificateManager.validate(json_data_2)

        self.assertIn('must have name of the certificate', context.exception)


@ddt.ddt
@override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
class CertificatesListHandlerTestCase(
        EventTestMixin, CourseTestCase, CertificatesBaseTestCase, HelperMethods, UrlResetMixin
):
    """
    Test cases for certificates_list_handler.
    """
    def setUp(self):
        """
        Set up CertificatesListHandlerTestCase.
        """
        super(CertificatesListHandlerTestCase, self).setUp('contentstore.views.certificates.tracker')
        self.reset_urls()

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
            u'is_active': True,
            u'signatories': []
        }
        response = self.client.ajax_post(
            self._url(),
            data=CERTIFICATE_JSON
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("Location", response)
        content = json.loads(response.content)
        certificate_id = self._remove_ids(content)
        self.assertEqual(content, expected)
        self.assert_event_emitted(
            'edx.certificate.configuration.created',
            course_id=unicode(self.course.id),
            configuration_id=certificate_id,
        )

    def test_cannot_create_certificate_if_user_has_no_write_permissions(self):
        """
        Tests user without write permissions on course should not able to create certificate
        """
        user = UserFactory()
        self.client.login(username=user.username, password='test')
        response = self.client.ajax_post(
            self._url(),
            data=CERTIFICATE_JSON
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(LMS_BASE=None)
    def test_no_lms_base_for_certificate_web_view_link(self):
        test_link = get_lms_link_for_certificate_web_view(
            user_id=self.user.id,
            course_key=self.course.id,
            mode='honor'
        )
        self.assertEquals(test_link, None)

    @override_settings(LMS_BASE="lms_base_url")
    def test_lms_link_for_certificate_web_view(self):
        test_url = "//lms_base_url/certificates/user/" \
                   + str(self.user.id) + "/course/" + unicode(self.course.id) + '?preview=honor'
        link = get_lms_link_for_certificate_web_view(
            user_id=self.user.id,
            course_key=self.course.id,
            mode='honor'
        )
        self.assertEquals(link, test_url)

    @mock.patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_certificate_info_in_response(self):
        """
        Test that certificate has been created and rendered properly with non-audit course mode.
        """
        CourseModeFactory.create(course_id=self.course.id, mode_slug='verified')
        response = self.client.ajax_post(
            self._url(),
            data=CERTIFICATE_JSON_WITH_SIGNATORIES
        )

        self.assertEqual(response.status_code, 201)

        # in html response
        result = self.client.get_html(self._url())
        self.assertIn('Test certificate', result.content)
        self.assertIn('Test description', result.content)

        # in JSON response
        response = self.client.get_json(self._url())
        data = json.loads(response.content)
        self.assertEquals(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test certificate')
        self.assertEqual(data[0]['description'], 'Test description')
        self.assertEqual(data[0]['version'], CERTIFICATE_SCHEMA_VERSION)

    @mock.patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_certificate_info_not_in_response(self):
        """
        Test that certificate has not been rendered audit only course mode.
        """
        response = self.client.ajax_post(
            self._url(),
            data=CERTIFICATE_JSON_WITH_SIGNATORIES
        )

        self.assertEqual(response.status_code, 201)

        # in html response
        result = self.client.get_html(self._url())
        self.assertNotIn('Test certificate', result.content)

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

    def test_audit_course_mode_is_skipped(self):
        """
        Tests audit course mode is skipped when rendering certificates page.
        """
        CourseModeFactory.create(course_id=self.course.id)
        CourseModeFactory.create(course_id=self.course.id, mode_slug='verified')
        response = self.client.get_html(
            self._url(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'verified')
        self.assertNotContains(response, 'audit')

    def test_audit_only_disables_cert(self):
        """
        Tests audit course mode is skipped when rendering certificates page.
        """
        CourseModeFactory.create(course_id=self.course.id, mode_slug='audit')
        response = self.client.get_html(
            self._url(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This course does not use a mode that offers certificates.')
        self.assertNotContains(response, 'This module is not enabled.')
        self.assertNotContains(response, 'Loading')

    @ddt.data(
        ['audit', 'verified'],
        ['verified'],
        ['audit', 'verified', 'credit'],
        ['verified', 'credit'],
        ['professional']
    )
    def test_non_audit_enables_cert(self, slugs):
        """
        Tests audit course mode is skipped when rendering certificates page.
        """
        for slug in slugs:
            CourseModeFactory.create(course_id=self.course.id, mode_slug=slug)
        response = self.client.get_html(
            self._url(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'This course does not use a mode that offers certificates.')
        self.assertNotContains(response, 'This module is not enabled.')
        self.assertContains(response, 'Loading')

    def test_assign_unique_identifier_to_certificates(self):
        """
        Test certificates have unique ids
        """
        self._add_course_certificates(count=2)
        json_data = {
            u'version': CERTIFICATE_SCHEMA_VERSION,
            u'name': u'New test certificate',
            u'description': u'New test description',
            u'is_active': True,
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


@ddt.ddt
@override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
class CertificatesDetailHandlerTestCase(
        EventTestMixin, CourseTestCase, CertificatesBaseTestCase, HelperMethods, UrlResetMixin
):
    """
    Test cases for CertificatesDetailHandlerTestCase.
    """

    _id = 0

    def setUp(self):  # pylint: disable=arguments-differ
        """
        Set up CertificatesDetailHandlerTestCase.
        """
        super(CertificatesDetailHandlerTestCase, self).setUp('contentstore.views.certificates.tracker')
        self.reset_urls()

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
            u'is_active': True,
            u'course_title': u'Course Title Override',
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
        self.assert_event_emitted(
            'edx.certificate.configuration.created',
            course_id=unicode(self.course.id),
            configuration_id=666,
        )

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
            u'is_active': True,
            u'course_title': u'Course Title Override',
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
        self.assert_event_emitted(
            'edx.certificate.configuration.modified',
            course_id=unicode(self.course.id),
            configuration_id=1,
        )
        self.reload_course()

        # Verify that certificate is properly updated in the course.
        course_certificates = self.course.certificates['certificates']
        self.assertEqual(len(course_certificates), 2)
        self.assertEqual(course_certificates[1].get('name'), u'New test certificate')
        self.assertEqual(course_certificates[1].get('description'), 'New test description')

    def test_can_edit_certificate_without_is_active(self):
        """
        Tests user should be able to edit certificate, if is_active attribute is not present
        for given certificate. Old courses might not have is_active attribute in certificate data.
        """
        certificates = [
            {
                'id': 1,
                'name': 'certificate with is_active',
                'description': 'Description ',
                'signatories': [],
                'version': CERTIFICATE_SCHEMA_VERSION,
            }
        ]
        self.course.certificates = {'certificates': certificates}
        self.save_course()

        expected = {
            u'id': 1,
            u'version': CERTIFICATE_SCHEMA_VERSION,
            u'name': u'New test certificate',
            u'description': u'New test description',
            u'is_active': True,
            u'course_title': u'Course Title Override',
            u'signatories': []

        }

        response = self.client.post(
            self._url(cid=1),
            data=json.dumps(expected),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content)
        self.assertEqual(content, expected)

    @ddt.data(C4X_SIGNATORY_PATH, SIGNATORY_PATH)
    def test_can_delete_certificate_with_signatories(self, signatory_path):
        """
        Delete certificate
        """
        self._add_course_certificates(count=2, signatory_count=1, asset_path_format=signatory_path)
        response = self.client.delete(
            self._url(cid=1),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 204)
        self.assert_event_emitted(
            'edx.certificate.configuration.deleted',
            course_id=unicode(self.course.id),
            configuration_id='1',
        )
        self.reload_course()
        # Verify that certificates are properly updated in the course.
        certificates = self.course.certificates['certificates']
        self.assertEqual(len(certificates), 1)
        self.assertEqual(certificates[0].get('name'), 'Name 0')
        self.assertEqual(certificates[0].get('description'), 'Description 0')

    def test_can_delete_certificate_with_slash_prefix_signatory(self):
        """
        Delete certificate
        """
        self._add_course_certificates(count=2, signatory_count=1, asset_path_format="/" + SIGNATORY_PATH)
        response = self.client.delete(
            self._url(cid=1),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 204)
        self.assert_event_emitted(
            'edx.certificate.configuration.deleted',
            course_id=unicode(self.course.id),
            configuration_id='1',
        )
        self.reload_course()
        # Verify that certificates are properly updated in the course.
        certificates = self.course.certificates['certificates']
        self.assertEqual(len(certificates), 1)
        self.assertEqual(certificates[0].get('name'), 'Name 0')
        self.assertEqual(certificates[0].get('description'), 'Description 0')

    @ddt.data("not_a_valid_asset_key{}.png", "/not_a_valid_asset_key{}.png")
    def test_can_delete_certificate_with_invalid_signatory(self, signatory_path):
        """
        Delete certificate
        """
        self._add_course_certificates(count=2, signatory_count=1, asset_path_format=signatory_path)
        response = self.client.delete(
            self._url(cid=1),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 204)
        self.assert_event_emitted(
            'edx.certificate.configuration.deleted',
            course_id=unicode(self.course.id),
            configuration_id='1',
        )
        self.reload_course()
        # Verify that certificates are properly updated in the course.
        certificates = self.course.certificates['certificates']
        self.assertEqual(len(certificates), 1)
        self.assertEqual(certificates[0].get('name'), 'Name 0')
        self.assertEqual(certificates[0].get('description'), 'Description 0')

    @ddt.data(C4X_SIGNATORY_PATH, SIGNATORY_PATH)
    def test_delete_certificate_without_write_permissions(self, signatory_path):
        """
        Tests certificate deletion without write permission on course.
        """
        self._add_course_certificates(count=2, signatory_count=1, asset_path_format=signatory_path)
        user = UserFactory()
        self.client.login(username=user.username, password='test')
        response = self.client.delete(
            self._url(cid=1),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 403)

    @ddt.data(C4X_SIGNATORY_PATH, SIGNATORY_PATH)
    def test_delete_certificate_without_global_staff_permissions(self, signatory_path):
        """
        Tests deletion of an active certificate without global staff permission on course.
        """
        self._add_course_certificates(count=2, signatory_count=1, is_active=True, asset_path_format=signatory_path)
        user = UserFactory()
        for role in [CourseInstructorRole, CourseStaffRole]:
            role(self.course.id).add_users(user)
        self.client.login(username=user.username, password='test')
        response = self.client.delete(
            self._url(cid=1),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 403)

    @ddt.data(C4X_SIGNATORY_PATH, SIGNATORY_PATH)
    def test_update_active_certificate_without_global_staff_permissions(self, signatory_path):
        """
        Tests update of an active certificate without global staff permission on course.
        """
        self._add_course_certificates(count=2, signatory_count=1, is_active=True, asset_path_format=signatory_path)
        cert_data = {
            u'id': 1,
            u'version': CERTIFICATE_SCHEMA_VERSION,
            u'name': u'New test certificate',
            u'description': u'New test description',
            u'course_title': u'Course Title Override',
            u'org_logo_path': '',
            u'is_active': False,
            u'signatories': []
        }
        user = UserFactory()
        for role in [CourseInstructorRole, CourseStaffRole]:
            role(self.course.id).add_users(user)
        self.client.login(username=user.username, password='test')
        response = self.client.put(
            self._url(cid=1),
            data=json.dumps(cert_data),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 403)

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

    @ddt.data(C4X_SIGNATORY_PATH, SIGNATORY_PATH)
    def test_can_delete_signatory(self, signatory_path):
        """
        Delete an existing certificate signatory
        """
        self._add_course_certificates(count=2, signatory_count=3, asset_path_format=signatory_path)
        certificates = self.course.certificates['certificates']
        signatory = certificates[1].get("signatories")[1]
        image_asset_location = AssetKey.from_string(signatory['signature_image_path'])
        content = contentstore().find(image_asset_location)
        self.assertIsNotNone(content)
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
        # make sure signatory signature image is deleted too
        self.assertRaises(NotFoundError, contentstore().find, image_asset_location)

    @ddt.data(C4X_SIGNATORY_PATH, SIGNATORY_PATH)
    def test_deleting_signatory_without_signature(self, signatory_path):
        """
        Delete an signatory whose signature image is already removed or does not exist
        """
        self._add_course_certificates(count=2, signatory_count=4, asset_path_format=signatory_path)
        test_url = '{}/signatories/3'.format(self._url(cid=1))
        response = self.client.delete(
            test_url,
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 204)

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

    @ddt.data(C4X_SIGNATORY_PATH, SIGNATORY_PATH)
    def test_certificate_activation_success(self, signatory_path):
        """
        Activate and Deactivate the course certificate
        """
        test_url = reverse_course_url('certificates.certificate_activation_handler', self.course.id)
        self._add_course_certificates(count=1, signatory_count=2, asset_path_format=signatory_path)

        is_active = True
        for i in range(2):
            if i == 1:
                is_active = not is_active
            response = self.client.post(
                test_url,
                data=json.dumps({"is_active": is_active}),
                content_type="application/json",
                HTTP_ACCEPT="application/json",
                HTTP_X_REQUESTED_WITH="XMLHttpRequest"
            )
            self.assertEquals(response.status_code, 200)
            course = self.store.get_course(self.course.id)
            certificates = course.certificates['certificates']
            self.assertEqual(certificates[0].get('is_active'), is_active)
            cert_event_type = 'activated' if is_active else 'deactivated'
            self.assert_event_emitted(
                '.'.join(['edx.certificate.configuration', cert_event_type]),
                course_id=unicode(self.course.id),
            )

    @ddt.data(*itertools.product([True, False], [C4X_SIGNATORY_PATH, SIGNATORY_PATH]))
    @ddt.unpack
    def test_certificate_activation_without_write_permissions(self, activate, signatory_path):
        """
        Tests certificate Activate and Deactivate should not be allowed if user
        does not have write permissions on course.
        """
        test_url = reverse_course_url('certificates.certificate_activation_handler', self.course.id)
        self._add_course_certificates(count=1, signatory_count=2, asset_path_format=signatory_path)
        user = UserFactory()
        self.client.login(username=user.username, password='test')
        response = self.client.post(
            test_url,
            data=json.dumps({"is_active": activate}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEquals(response.status_code, 403)

    @ddt.data(C4X_SIGNATORY_PATH, SIGNATORY_PATH)
    def test_certificate_activation_failure(self, signatory_path):
        """
        Certificate activation should fail when user has not read access to course then permission denied exception
        should raised.
        """
        test_url = reverse_course_url('certificates.certificate_activation_handler', self.course.id)
        test_user_client, test_user = self.create_non_staff_authed_user_client()
        CourseEnrollment.enroll(test_user, self.course.id)
        self._add_course_certificates(count=1, signatory_count=2, asset_path_format=signatory_path)
        response = test_user_client.post(
            test_url,
            data=json.dumps({"is_active": True}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEquals(response.status_code, 403)
        course = self.store.get_course(self.course.id)
        certificates = course.certificates['certificates']
        self.assertEqual(certificates[0].get('is_active'), False)
