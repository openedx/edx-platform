"""Tests for certificates views. """

import json
from uuid import uuid4
from nose.plugins.attrib import attr
from mock import patch

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.utils import override_settings

from openedx.core.lib.tests.assertions.events import assert_event_matches
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from track.tests import EventTrackingTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from certificates.api import get_certificate_url
from certificates.models import (
    GeneratedCertificate,
    BadgeAssertion,
    CertificateStatuses,
    CertificateSocialNetworks,
    CertificateTemplate,
)

from certificates.tests.factories import (
    CertificateHtmlViewConfigurationFactory,
    LinkedInAddToProfileConfigurationFactory,
)
from util import organizations_helpers as organizations_api
from django.test.client import RequestFactory
import urllib

FEATURES_WITH_CERTS_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_ENABLED['CERTIFICATES_HTML_VIEW'] = True

FEATURES_WITH_CERTS_DISABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_DISABLED['CERTIFICATES_HTML_VIEW'] = False

FEATURES_WITH_CUSTOM_CERTS_ENABLED = {
    "CUSTOM_CERTIFICATE_TEMPLATES_ENABLED": True
}
FEATURES_WITH_CUSTOM_CERTS_ENABLED.update(FEATURES_WITH_CERTS_ENABLED)


@attr('shard_1')
class CertificatesViewsTests(ModuleStoreTestCase, EventTrackingTestCase):
    """
    Tests for the certificates web/html views
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
        self.request = RequestFactory().request()

        self.cert = GeneratedCertificate.objects.create(
            user=self.user,
            course_id=self.course_id,
            verify_uuid=uuid4(),
            download_uuid=uuid4(),
            download_url="http://www.example.com/certificates/download",
            grade="0.95",
            key='the_key',
            distinction=True,
            status='generated',
            mode='honor',
            name=self.user.profile.name,
        )
        CourseEnrollmentFactory.create(
            user=self.user,
            course_id=self.course_id
        )
        CertificateHtmlViewConfigurationFactory.create()
        LinkedInAddToProfileConfigurationFactory.create()

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
                'org_logo_path': '/t4x/orgX/testX/asset/org-logo-{}.png'.format(i),
                'signatories': signatories,
                'version': 1,
                'is_active': is_active
            } for i in xrange(count)
        ]

        self.course.certificates = {'certificates': certificates}
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)

    def _create_custom_template(self, org_id=None, mode=None, course_key=None):
        """
        Creates a custom certificate template entry in DB.
        """
        template_html = """
            <html>
            <body>
                lang: ${LANGUAGE_CODE}
                course name: ${accomplishment_copy_course_name}
                mode: ${course_mode}
                ${accomplishment_copy_course_description}
            </body>
            </html>
        """
        template = CertificateTemplate(
            name='custom template',
            template=template_html,
            organization_id=org_id,
            course_key=course_key,
            mode=mode,
            is_active=True
        )
        template.save()

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_linkedin_share_url(self):
        """
        Test: LinkedIn share URL.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url)
        self.assertTrue(urllib.quote_plus(self.request.build_absolute_uri(test_url)) in response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_rendering_course_organization_data(self):
        """
        Test: organization data should render on certificate web view if course has organization.
        """
        test_organization_data = {
            'name': 'test organization',
            'short_name': 'test_organization',
            'description': 'Test Organization Description',
            'active': True,
            'logo': '/logo_test1.png/'
        }
        test_org = organizations_api.add_organization(organization_data=test_organization_data)
        organizations_api.add_organization_course(organization_data=test_org, course_id=unicode(self.course.id))
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url)
        self.assertIn(
            'a course of study offered by test_organization, an online learning initiative of test organization',
            response.content
        )
        self.assertNotIn(
            'a course of study offered by testorg',
            response.content
        )
        self.assertIn(
            '<title>test_organization {} Certificate |'.format(self.course.number, ),
            response.content
        )
        self.assertIn('logo_test1.png', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_valid_certificate(self):
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        self._add_course_certificates(count=1, signatory_count=2)
        response = self.client.get(test_url)
        self.assertIn(str(self.cert.verify_uuid), response.content)

        # Hit any "verified" mode-specific branches
        self.cert.mode = 'verified'
        self.cert.save()
        response = self.client.get(test_url)
        self.assertIn(str(self.cert.verify_uuid), response.content)

        # Hit any 'xseries' mode-specific branches
        self.cert.mode = 'xseries'
        self.cert.save()
        response = self.client.get(test_url)
        self.assertIn(str(self.cert.verify_uuid), response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_with_valid_signatories(self):
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        self._add_course_certificates(count=1, signatory_count=2)
        response = self.client.get(test_url)
        self.assertIn('course_title_0', response.content)
        self.assertIn('Signatory_Name 0', response.content)
        self.assertIn('Signatory_Title 0', response.content)
        self.assertIn('Signatory_Organization 0', response.content)
        self.assertIn('/static/certificates/images/demo-sig0.png', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_course_display_name_not_override_with_course_title(self):
        # if certificate in descriptor has not course_title then course name should not be overridden with this title.
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        test_certificates = [
            {
                'id': 0,
                'name': 'Name 0',
                'description': 'Description 0',
                'signatories': [],
                'version': 1,
                'is_active':True
            }
        ]
        self.course.certificates = {'certificates': test_certificates}
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)
        response = self.client.get(test_url)
        self.assertNotIn('test_course_title_0', response.content)
        self.assertIn('refundable course', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_certificate_view_without_org_logo(self):
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        test_certificates = [
            {
                'id': 0,
                'name': 'Certificate Name 0',
                'signatories': [],
                'version': 1,
                'is_active': True
            }
        ]
        self.course.certificates = {'certificates': test_certificates}
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)
        response = self.client.get(test_url)
        # make sure response html has only one organization logo container for edX
        self.assertContains(response, "<li class=\"wrapper-organization\">", 1)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_without_signatories(self):
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course)
        )
        self._add_course_certificates(count=1, signatory_count=0)
        response = self.client.get(test_url)
        self.assertNotIn('Signatory_Name 0', response.content)
        self.assertNotIn('Signatory_Title 0', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_DISABLED)
    def test_render_html_view_disabled_feature_flag_returns_static_url(self):
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        self.assertIn(str(self.cert.download_url), test_url)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_course_id(self):
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id='az/23423/4vs'
        )

        response = self.client.get(test_url)
        self.assertIn('invalid', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_course(self):
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id='missing/course/key'
        )
        response = self.client.get(test_url)
        self.assertIn('invalid', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_user(self):
        test_url = get_certificate_url(
            user_id=111,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url)
        self.assertIn('invalid', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_user_certificate(self):
        self.cert.delete()
        self.assertEqual(len(GeneratedCertificate.objects.all()), 0)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url)
        self.assertIn('invalid', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_with_preview_mode(self):
        """
        test certificate web view should render properly along with its signatories information when accessing it in
        preview mode. Either the certificate is marked active or not.
        """
        self.cert.delete()
        self.assertEqual(len(GeneratedCertificate.objects.all()), 0)
        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url + '?preview=honor')
        self.assertNotIn(self.course.display_name, response.content)
        self.assertIn('course_title_0', response.content)
        self.assertIn('Signatory_Title 0', response.content)

        # mark certificate inactive but accessing in preview mode.
        self._add_course_certificates(count=1, signatory_count=2, is_active=False)
        response = self.client.get(test_url + '?preview=honor')
        self.assertNotIn(self.course.display_name, response.content)
        self.assertIn('course_title_0', response.content)
        self.assertIn('Signatory_Title 0', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_certificate_configuration(self):
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url)
        self.assertIn("Invalid Certificate", response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_certificate_evidence_event_emitted(self):
        self.client.logout()
        self._add_course_certificates(count=1, signatory_count=2)
        self.recreate_tracker()
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        actual_event = self.get_event()
        self.assertEqual(actual_event['name'], 'edx.certificate.evidence_visited')
        assert_event_matches(
            {
                'user_id': self.user.id,
                'certificate_id': unicode(self.cert.verify_uuid),
                'enrollment_mode': self.cert.mode,
                'certificate_url': test_url,
                'course_id': unicode(self.course.id),
                'social_network': CertificateSocialNetworks.linkedin
            },
            actual_event['data']
        )

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_evidence_event_sent(self):
        cert_url = get_certificate_url(
            user_id=self.user.id,
            course_id=self.course_id
        )
        test_url = '{}?evidence_visit=1'.format(cert_url)
        self._add_course_certificates(count=1, signatory_count=2)
        self.recreate_tracker()
        assertion = BadgeAssertion(
            user=self.user, course_id=self.course_id, mode='honor',
            data={
                'image': 'http://www.example.com/image.png',
                'json': {'id': 'http://www.example.com/assertion.json'},
                'issuer': 'http://www.example.com/issuer.json',

            }
        )
        assertion.save()
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        assert_event_matches(
            {
                'name': 'edx.badge.assertion.evidence_visited',
                'data': {
                    'course_id': 'testorg/run1/refundable_course',
                    # pylint: disable=no-member
                    'assertion_id': assertion.id,
                    'assertion_json_url': 'http://www.example.com/assertion.json',
                    'assertion_image_url': 'http://www.example.com/image.png',
                    'user_id': self.user.id,
                    'issuer': 'http://www.example.com/issuer.json',
                    'enrollment_mode': 'honor',
                },
            },
            self.get_event()
        )

    @override_settings(FEATURES=FEATURES_WITH_CERTS_DISABLED)
    def test_request_certificate_without_passing(self):
        self.cert.status = CertificateStatuses.unavailable
        self.cert.save()
        request_certificate_url = reverse('certificates.views.request_certificate')
        response = self.client.post(request_certificate_url, {'course_id': unicode(self.course.id)})
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(CertificateStatuses.notpassing, response_json['add_status'])

    @override_settings(FEATURES=FEATURES_WITH_CERTS_DISABLED)
    @override_settings(CERT_QUEUE='test-queue')
    def test_request_certificate_after_passing(self):
        self.cert.status = CertificateStatuses.unavailable
        self.cert.save()
        request_certificate_url = reverse('certificates.views.request_certificate')
        with patch('capa.xqueue_interface.XQueueInterface.send_to_queue') as mock_queue:
            mock_queue.return_value = (0, "Successfully queued")
            with patch('courseware.grades.grade') as mock_grade:
                mock_grade.return_value = {'grade': 'Pass', 'percent': 0.75}
                response = self.client.post(request_certificate_url, {'course_id': unicode(self.course.id)})
                self.assertEqual(response.status_code, 200)
                response_json = json.loads(response.content)
                self.assertEqual(CertificateStatuses.generating, response_json['add_status'])

    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    @override_settings(LANGUAGE_CODE='fr')
    def test_certificate_custom_template_with_org_mode_course(self):
        """
        Tests custom template search and rendering.
        This test should check template matching when org={org}, course={course}, mode={mode}.
        """
        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_template(org_id=1, mode='honor', course_key=unicode(self.course.id))
        self._create_custom_template(org_id=2, mode='honor')
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )

        with patch('certificates.api.get_course_organizations') as mock_get_orgs:
            mock_get_orgs.side_effect = [
                [{"id": 1, "name": "organization name"}],
                [{"id": 2, "name": "organization name 2"}],
            ]
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'lang: fr')
            self.assertContains(response, 'course name: course_title_0')
            # test with second organization template
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'lang: fr')
            self.assertContains(response, 'course name: course_title_0')

    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    def test_certificate_custom_template_with_org(self):
        """
        Tests custom template search if we have a single template for organization and mode
        with course set to Null.
        This test should check template matching when org={org}, course=Null, mode={mode}.
        """
        course = CourseFactory.create(
            org='cstX', number='cst_22', display_name='custom template course'
        )

        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_template(org_id=1, mode='honor')
        self._create_custom_template(org_id=1, mode='honor', course_key=course.id)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )

        with patch('certificates.api.get_course_organizations') as mock_get_orgs:
            mock_get_orgs.side_effect = [
                [{"id": 1, "name": "organization name"}],
            ]
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'course name: course_title_0')

    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    def test_certificate_custom_template_with_organization(self):
        """
        Tests custom template search when we have a single template for a organization.
        This test should check template matching when org={org}, course=Null, mode=null.
        """
        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_template(org_id=1, mode='honor')
        self._create_custom_template(org_id=1, mode='honor', course_key=self.course.id)
        self._create_custom_template(org_id=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )

        with patch('certificates.api.get_course_organizations') as mock_get_orgs:
            mock_get_orgs.side_effect = [
                [{"id": 2, "name": "organization name 2"}],
            ]
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)

    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    def test_certificate_custom_template_with_course_mode(self):
        """
        Tests custom template search if we have a single template for a course mode.
        This test should check template matching when org=null, course=Null, mode={mode}.
        """
        mode = 'honor'
        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_template(mode=mode)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )

        with patch('certificates.api.get_course_organizations') as mock_get_orgs:
            mock_get_orgs.return_value = []
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'mode: {}'.format(mode))
