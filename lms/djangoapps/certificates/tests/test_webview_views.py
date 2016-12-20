# -*- coding: utf-8 -*-
"""Tests for certificates views. """

import json
import ddt
import mock
from uuid import uuid4
from nose.plugins.attrib import attr
from mock import patch
from urllib import urlencode
from collections import OrderedDict

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.utils import override_settings

from course_modes.models import CourseMode
from openedx.core.lib.tests.assertions.events import assert_event_matches
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from student.roles import CourseStaffRole
from track.tests import EventTrackingTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from certificates.api import get_certificate_url
from certificates.models import (
    GeneratedCertificate,
    CertificateStatuses,
    CertificateSocialNetworks,
    CertificateTemplate,
    CertificateHtmlViewConfiguration,
    CertificateTemplateAsset,
)

from certificates.tests.factories import (
    CertificateHtmlViewConfigurationFactory,
    LinkedInAddToProfileConfigurationFactory,
    BadgeAssertionFactory,
    GeneratedCertificateFactory,
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


def _fake_is_request_in_microsite():
    """
    Mocked version of microsite helper method to always return true
    """
    return True


@attr('shard_1')
@ddt.ddt
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
        self.linknedin_url = 'http://www.linkedin.com/profile/add?{params}'

        self.cert = GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course_id,
            download_uuid=uuid4(),
            download_url="http://www.example.com/certificates/download",
            grade="0.95",
            key='the_key',
            distinction=True,
            status='downloadable',
            mode='honor',
            name=self.user.profile.name,
        )
        CourseEnrollmentFactory.create(
            user=self.user,
            course_id=self.course_id,
            mode=CourseMode.HONOR,
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
                'id': i
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
            <%namespace name='static' file='static_content.html'/>
            <html>
            <body>
                lang: ${LANGUAGE_CODE}
                course name: ${accomplishment_copy_course_name}
                mode: ${course_mode}
                ${accomplishment_copy_course_description}
                ${twitter_url}
                <img class="custom-logo" src="${static.certificate_asset_url('custom-logo')}" />
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
        test_url = get_certificate_url(course_id=self.course.id, uuid=self.cert.verify_uuid)
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        params = OrderedDict([
            ('_ed', '0_0dPSPyS070e0HsE9HNz_13_d11_',),
            ('pfCertificationName', '{platform_name} Honor Code Certificate for {course_name}'.format(
                platform_name=settings.PLATFORM_NAME,
                course_name=self.course.display_name,
            ),),
            ('pfCertificationUrl', self.request.build_absolute_uri(test_url),),
        ])
        self.assertIn(
            self.linknedin_url.format(params=urlencode(params)),
            response.content
        )

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_linkedin_share_microsites(self):
        """
        Test: LinkedIn share URL should be visible when called from within a microsite.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(course_id=self.cert.course_id, uuid=self.cert.verify_uuid)
        response = self.client.get(test_url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEqual(response.status_code, 200)
        # the linkedIn share URL with appropriate parameters should be present
        params = OrderedDict([
            ('_ed', settings.MICROSITE_CONFIGURATION['test_microsite']['LINKEDIN_COMPANY_ID'],),
            ('pfCertificationName', '{platform_name} Honor Code Certificate for {course_name}'.format(
                platform_name=settings.MICROSITE_CONFIGURATION['test_microsite']['platform_name'],
                course_name=self.course.display_name,
            ),),
            ('pfCertificationUrl', 'http://' + settings.MICROSITE_TEST_HOSTNAME + test_url,),
        ])
        self.assertIn(
            self.linknedin_url.format(params=urlencode(params)),
            response.content
        )

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    @patch.dict("django.conf.settings.SOCIAL_SHARING_SETTINGS", {"CERTIFICATE_FACEBOOK": True})
    def test_facebook_share_microsites(self):
        """
        Test: Facebook share URL should be visible when web cert called from within a white label
        site and it should use white label site's FACEBOOK_APP_ID.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(course_id=self.cert.course_id, uuid=self.cert.verify_uuid)
        response = self.client.get(test_url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Post on Facebook", response.content)
        self.assertIn(settings.MICROSITE_CONFIGURATION['test_microsite']['FACEBOOK_APP_ID'], response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    @ddt.data(
        (False, False, False),
        (False, False, True),
        (False, True, True),
        (True, True, True),
        (True, True, False),
    )
    @ddt.unpack
    def test_social_sharing_availablity_microsites(self, facebook_sharing, twitter_sharing, linkedin_sharing):
        """
        Test: Facebook, Twitter and LinkedIn sharing availability for microsites.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(course_id=self.cert.course_id, uuid=self.cert.verify_uuid)
        social_sharing_settings = dict(
            CERTIFICATE_FACEBOOK=facebook_sharing,
            CERTIFICATE_TWITTER=twitter_sharing,
            CERTIFICATE_LINKEDIN=linkedin_sharing,
        )
        with patch("django.conf.settings.MICROSITE_CONFIGURATION", {
            "test_microsite": dict(
                settings.MICROSITE_CONFIGURATION['test_microsite'],
                SOCIAL_SHARING_SETTINGS=social_sharing_settings,
            )
        }):
            response = self.client.get(test_url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
            self.assertEqual(response.status_code, 200)
            self.assertEqual("Post on Facebook" in response.content, facebook_sharing)
            self.assertEqual("Share on Twitter" in response.content, twitter_sharing)
            self.assertEqual("Add to LinkedIn Profile" in response.content, linkedin_sharing)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_facebook_default_text_microsites(self):
        """
        Test: Facebook sharing default text for microsites.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(course_id=self.cert.course_id, uuid=self.cert.verify_uuid)
        facebook_text = "Facebook text on Test Microsite"
        social_sharing_settings = dict(
            CERTIFICATE_FACEBOOK=True,
            CERTIFICATE_FACEBOOK_TEXT=facebook_text,
        )
        with patch("django.conf.settings.MICROSITE_CONFIGURATION", {
            "test_microsite": dict(
                settings.MICROSITE_CONFIGURATION['test_microsite'],
                SOCIAL_SHARING_SETTINGS=social_sharing_settings,
            )
        }):
            response = self.client.get(test_url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
            self.assertContains(response, facebook_text)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_twitter_default_text_microsites(self):
        """
        Test: Twitter sharing default text for microsites.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(course_id=self.cert.course_id, uuid=self.cert.verify_uuid)
        twitter_text = "Twitter text on Test Microsite"
        social_sharing_settings = dict(
            CERTIFICATE_TWITTER=True,
            CERTIFICATE_TWITTER_TEXT=twitter_text,
        )
        with patch("django.conf.settings.MICROSITE_CONFIGURATION", {
            "test_microsite": dict(
                settings.MICROSITE_CONFIGURATION['test_microsite'],
                SOCIAL_SHARING_SETTINGS=social_sharing_settings,
            )
        }):
            response = self.client.get(test_url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
            self.assertContains(response, twitter_text)

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
    @patch.dict("django.conf.settings.SOCIAL_SHARING_SETTINGS", {
        "CERTIFICATE_TWITTER": True,
        "CERTIFICATE_FACEBOOK": True,
    })
    @patch.dict("django.conf.settings.MICROSITE_CONFIGURATION", {
        "test_microsite": dict(
            settings.MICROSITE_CONFIGURATION['test_microsite'],
            urls=dict(
                ABOUT=None,
                PRIVACY=None,
                TOS_AND_HONOR=None,
            ),
        )
    })
    @patch.dict("django.conf.settings.MKTG_URL_LINK_MAP", {
        'ABOUT': None,
        'PRIVACY': None,
        'TOS_AND_HONOR': None,
    })
    def test_rendering_maximum_data(self):
        """
        Tests at least one data item from different context update methods to
        make sure every context update method is invoked while rendering certificate template.
        """
        long_org_name = 'Long org name'
        short_org_name = 'short_org_name'
        test_organization_data = {
            'name': long_org_name,
            'short_name': short_org_name,
            'description': 'Test Organization Description',
            'active': True,
            'logo': '/logo_test1.png'
        }
        test_org = organizations_api.add_organization(organization_data=test_organization_data)
        organizations_api.add_organization_course(organization_data=test_org, course_id=unicode(self.course.id))
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        BadgeAssertionFactory.create(
            user=self.user, course_id=self.course_id,
        )
        self.course.cert_html_view_overrides = {
            "logo_src": "/static/certificates/images/course_override_logo.png"
        }

        self.course.save()
        self.store.update_item(self.course, self.user.id)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)

        # Test an item from basic info
        self.assertIn(
            'Terms of Service &amp; Honor Code',
            response.content
        )
        self.assertIn(
            'Certificate ID Number',
            response.content
        )
        # Test an item from html cert configuration
        self.assertIn(
            '<a class="logo" href="http://test_microsite.localhost">',
            response.content
        )
        # Test an item from course info
        self.assertIn(
            'course_title_0',
            response.content
        )
        # Test an item from user info
        self.assertIn(
            "{fullname}, you earned a certificate!".format(fullname=self.user.profile.name),
            response.content
        )
        # Test an item from social info
        self.assertIn(
            "Post on Facebook",
            response.content
        )
        self.assertIn(
            "Share on Twitter",
            response.content
        )
        # Test an item from certificate/org info
        self.assertIn(
            "a course of study offered by {partner_short_name}, "
            "an online learning initiative of "
            "{partner_long_name}.".format(
                partner_short_name=short_org_name,
                partner_long_name=long_org_name,
                platform_name='Test Microsite'
            ),
            response.content
        )
        # Test item from badge info
        self.assertIn(
            "Add to Mozilla Backpack",
            response.content
        )
        # Test item from microsite info
        self.assertIn(
            "http://www.testmicrosite.org/about-us",
            response.content
        )
        # Test course overrides
        self.assertIn(
            "/static/certificates/images/course_override_logo.png",
            response.content
        )

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_valid_certificate(self):
        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
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
    def test_render_certificate_only_for_downloadable_status(self):
        """
        Tests taht Certificate HTML Web View returns Certificate only if certificate status is 'downloadable',
        for other statuses it should return "Invalid Certificate".
        """
        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )

        # Validate certificate
        response = self.client.get(test_url)
        self.assertIn(str(self.cert.verify_uuid), response.content)

        # Change status to 'generating' and validate that Certificate Web View returns "Invalid Certificate"
        self.cert.status = CertificateStatuses.generating
        self.cert.save()
        response = self.client.get(test_url)
        self.assertIn("Invalid Certificate", response.content)
        self.assertIn("Cannot Find Certificate", response.content)
        self.assertIn("We cannot find a certificate with this URL or ID number.", response.content)

    @ddt.data(
        (CertificateStatuses.downloadable, True),
        (CertificateStatuses.audit_passing, False),
        (CertificateStatuses.audit_notpassing, False),
    )
    @ddt.unpack
    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_audit_certificate_display(self, status, eligible_for_certificate):
        """
        Ensure that audit-mode certs are only shown in the web view if they
        are eligible for a certificate.
        """
        # Convert the cert to audit, with the specified eligibility
        self.cert.mode = 'audit'
        self.cert.status = status
        self.cert.save()

        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url)

        if eligible_for_certificate:
            self.assertIn(str(self.cert.verify_uuid), response.content)
        else:
            self.assertIn("Invalid Certificate", response.content)
            self.assertIn("Cannot Find Certificate", response.content)
            self.assertIn("We cannot find a certificate with this URL or ID number.", response.content)
            self.assertNotIn(str(self.cert.verify_uuid), response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_html_view_for_invalid_certificate(self):
        """
        Tests that Certificate HTML Web View returns "Cannot Find Certificate" if certificate has been invalidated.
        """
        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )

        # Validate certificate
        response = self.client.get(test_url)
        self.assertIn(str(self.cert.verify_uuid), response.content)

        # invalidate certificate and verify that "Cannot Find Certificate" is returned
        self.cert.invalidate()
        response = self.client.get(test_url)
        self.assertIn("Invalid Certificate", response.content)
        self.assertIn("Cannot Find Certificate", response.content)
        self.assertIn("We cannot find a certificate with this URL or ID number.", response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_with_valid_signatories(self):
        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )

        response = self.client.get(test_url)
        self.assertIn('course_title_0', response.content)
        self.assertIn('Signatory_Name 0', response.content)
        self.assertIn('Signatory_Title 0', response.content)
        self.assertIn('Signatory_Organization 0', response.content)
        self.assertIn('/static/certificates/images/demo-sig0.png', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_course_display_name_not_override_with_course_title(self):
        # if certificate in descriptor has not course_title then course name should not be overridden with this title.
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
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )

        response = self.client.get(test_url)
        self.assertNotIn('test_course_title_0', response.content)
        self.assertIn('refundable course', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_course_display_overrides(self):
        """
        Tests if `Course Number Display String` or `Course Organization Display` is set for a course
        in advance settings
        Then web certificate should display that course number and course org set in advance
        settings instead of original course number and course org.
        """
        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )

        self.course.display_coursenumber = "overridden_number"
        self.course.display_organization = "overridden_org"
        self.store.update_item(self.course, self.user.id)

        response = self.client.get(test_url)
        self.assertIn('overridden_number', response.content)
        self.assertIn('overridden_org', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_certificate_view_without_org_logo(self):
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

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url)
        # make sure response html has only one organization logo container for edX
        self.assertContains(response, "<li class=\"wrapper-organization\">", 1)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_without_signatories(self):
        self._add_course_certificates(count=1, signatory_count=0)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course)
        )
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
    def test_render_html_view_invalid_course(self):
        test_url = "/certificates/user/{user_id}/course/{course_id}".format(
            user_id=self.user.id,
            course_id="missing/course/key"
        )
        response = self.client.get(test_url)
        self.assertIn('invalid', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_user(self):
        self._add_course_certificates(count=1, signatory_count=0)
        test_url = get_certificate_url(
            user_id=111,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url)
        self.assertIn('invalid', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_user_certificate(self):
        self._add_course_certificates(count=1, signatory_count=0)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        self.cert.delete()
        self.assertEqual(len(GeneratedCertificate.eligible_certificates.all()), 0)

        response = self.client.get(test_url)
        self.assertIn('invalid', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED, PLATFORM_NAME=u'Űńíćődé Űńívéŕśítӳ')
    def test_render_html_view_with_unicode_platform_name(self):
        self._add_course_certificates(count=1, signatory_count=0)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_with_preview_mode(self):
        """
        test certificate web view should render properly along with its signatories information when accessing it in
        preview mode. Either the certificate is marked active or not.
        """
        self.cert.delete()
        self.assertEqual(len(GeneratedCertificate.eligible_certificates.all()), 0)
        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url + '?preview=honor')
        # accessing certificate web view in preview mode without
        # staff or instructor access should show invalid certificate
        self.assertIn('Cannot Find Certificate', response.content)

        CourseStaffRole(self.course.id).add_users(self.user)

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
    def test_render_html_view_with_preview_mode_when_user_already_has_cert(self):
        """
        test certificate web view should render properly in
        preview mode even if user who is previewing already has a certificate
        generated with different mode.
        """
        self._add_course_certificates(count=1, signatory_count=2)
        CourseStaffRole(self.course.id).add_users(self.user)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        # user has already has certificate generated for 'honor' mode
        # so let's try to preview in 'verified' mode.
        response = self.client.get(test_url + '?preview=verified')
        self.assertNotIn(self.course.display_name, response.content)
        self.assertIn('course_title_0', response.content)
        self.assertIn('Signatory_Title 0', response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_certificate_configuration(self):
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url)
        self.assertIn("Invalid Certificate", response.content)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_500_view_invalid_certificate_configuration(self):
        self._add_course_certificates(count=1, signatory_count=2)
        CertificateHtmlViewConfiguration.objects.all().update(enabled=False)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url + "?preview=honor")
        self.assertIn("Invalid Certificate Configuration", response.content)

        # Verify that Exception is raised when certificate is not in the preview mode
        with self.assertRaises(Exception):
            self.client.get(test_url)

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
        self._add_course_certificates(count=1, signatory_count=2)

        cert_url = get_certificate_url(
            user_id=self.user.id,
            course_id=self.course_id
        )
        test_url = '{}?evidence_visit=1'.format(cert_url)
        self.recreate_tracker()
        assertion = BadgeAssertionFactory.create(
            user=self.user, course_id=self.course_id,
        )
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        assert_event_matches(
            {
                'name': 'edx.badge.assertion.evidence_visited',
                'data': {
                    'course_id': 'testorg/run1/refundable_course',
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

    @ddt.data(True, False)
    def test_certificate_custom_template_with_unicode_data(self, custom_certs_enabled):
        """
        Tests custom template renders properly with unicode data.
        """
        mode = 'honor'
        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_template(mode=mode)
        with patch.dict("django.conf.settings.FEATURES", {
            "CERTIFICATES_HTML_VIEW": True,
            "CUSTOM_CERTIFICATE_TEMPLATES_ENABLED": custom_certs_enabled
        }):
            test_url = get_certificate_url(
                user_id=self.user.id,
                course_id=unicode(self.course.id)
            )
            with patch.dict("django.conf.settings.SOCIAL_SHARING_SETTINGS", {
                "CERTIFICATE_TWITTER": True,
                "CERTIFICATE_TWITTER_TEXT": u"nền tảng học tập"
            }):
                with patch('django.http.HttpRequest.build_absolute_uri') as mock_abs_uri:
                    mock_abs_uri.return_value = '='.join(['http://localhost/?param', u'é'])
                    with patch('certificates.api.get_course_organizations') as mock_get_orgs:
                        mock_get_orgs.return_value = []
                        response = self.client.get(test_url)
                        self.assertEqual(response.status_code, 200)
                        if custom_certs_enabled:
                            self.assertContains(response, 'mode: {}'.format(mode))
                        else:
                            self.assertContains(response, "Tweet this Accomplishment")
                        self.assertContains(response, 'https://twitter.com/intent/tweet')

    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    def test_certificate_asset_by_slug(self):
        """
        Tests certificate template asset display by slug using static.certificate_asset_url method.
        """
        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_template(mode='honor')
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )

        # render certificate without template asset
        with patch('certificates.api.get_course_organizations') as mock_get_orgs:
            mock_get_orgs.return_value = []
            response = self.client.get(test_url)
            self.assertContains(response, '<img class="custom-logo" src="" />')

        template_asset = CertificateTemplateAsset(
            description='custom logo',
            asset='certificate_template_assets/32/test_logo.png',
            asset_slug='custom-logo',
        )
        template_asset.save()

        # render certificate with template asset
        with patch('certificates.api.get_course_organizations') as mock_get_orgs:
            mock_get_orgs.return_value = []
            response = self.client.get(test_url)
            self.assertContains(
                response, '<img class="custom-logo" src="{}certificate_template_assets/32/test_logo.png" />'.format(
                    settings.MEDIA_URL
                )
            )

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_certificate_branding(self):
        """
        Test that link urls in certificate web view are customized according to site branding and
        microsite configuration.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)

        self.course.save()
        self.store.update_item(self.course, self.user.id)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        # logo_image_url Tis present in MICROSITE_CONFIGURATION['test_microsite']["urls"],
        #  so web certificate will use that.
        self.assertContains(
            response,
            settings.MICROSITE_CONFIGURATION['test_microsite']['logo_image_url'],
        )
        # ABOUT is present in MICROSITE_CONFIGURATION['test_microsite']["urls"] so web certificate will use that url.
        self.assertContains(
            response,
            settings.MICROSITE_CONFIGURATION['test_microsite']["urls"]['ABOUT'],
        )
        # PRIVACY is present in MICROSITE_CONFIGURATION['test_microsite']["urls"] so web certificate will use that url.
        self.assertContains(
            response,
            settings.MICROSITE_CONFIGURATION['test_microsite']["urls"]['PRIVACY'],
        )
        # TOS_AND_HONOR is present in MICROSITE_CONFIGURATION['test_microsite']["urls"],
        #  so web certificate will use that url.
        self.assertContains(
            response,
            settings.MICROSITE_CONFIGURATION['test_microsite']["urls"]['TOS_AND_HONOR'],
        )

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    @patch.dict("django.conf.settings.MICROSITE_CONFIGURATION", {
        "test_microsite": dict(
            settings.MICROSITE_CONFIGURATION['test_microsite'],
            urls=dict(
                ABOUT=None,
                PRIVACY=None,
                TOS_AND_HONOR=None,
            ),
        )
    })
    def test_certificate_branding_without_microsite_urls(self):
        """
        Test that links from MKTG_URL_LINK_MAP setting are used if corresponding microsite urls are not present.
        microsite configuration.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        self.course.save()
        self.store.update_item(self.course, self.user.id)
        configuration = CertificateHtmlViewConfiguration.get_config()
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
        # ABOUT is not present in MICROSITE_CONFIGURATION['test_microsite']["urls"],
        #  so web certificate will use MKTG_URL_LINK_MAP['ABOUT'] url.
        self.assertContains(
            response,
            settings.MKTG_URL_LINK_MAP['ABOUT'],
        )
        # PRIVACY is not present in MICROSITE_CONFIGURATION['test_microsite']["urls"],
        # so web certificate will use MKTG_URL_LINK_MAP['PRIVACY'] url.
        self.assertContains(
            response,
            settings.MKTG_URL_LINK_MAP['PRIVACY'],
        )
        # TOS_AND_HONOR is not present in MICROSITE_CONFIGURATION['test_microsite']["urls"] or MKTG_URL_LINK_MAP,
        # so web certificate will use CertificateHtmlViewConfiguration url.
        self.assertContains(
            response,
            configuration['microsites']['testmicrosite']['company_tos_url'],
        )

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    @patch.dict("django.conf.settings.MICROSITE_CONFIGURATION", {
        "test_microsite": dict(
            settings.MICROSITE_CONFIGURATION['test_microsite'],
            urls=dict(
                ABOUT=None,
                PRIVACY=None,
                TOS_AND_HONOR=None,
            ),
        )
    })
    @patch.dict("django.conf.settings.MKTG_URL_LINK_MAP", {
        'ABOUT': None,
        'PRIVACY': None,
        'TOS_AND_HONOR': None,
    })
    def test_certificate_without_branding_urls(self):
        """
        Test that links from CertificateHtmlViewConfiguration are used if
        corresponding microsite or marketing urls are not present.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)

        self.course.save()
        self.store.update_item(self.course, self.user.id)
        configuration = CertificateHtmlViewConfiguration.get_config()

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id)
        )
        response = self.client.get(test_url, HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)

        # ABOUT is not present in MICROSITE_CONFIGURATION['test_microsite']["urls"] or MKTG_URL_LINK_MAP,
        #  so web certificate will use CertificateHtmlViewConfiguration url.
        self.assertContains(
            response,
            configuration['microsites']['testmicrosite']['company_about_url'],
        )
        # PRIVACY is not present in MICROSITE_CONFIGURATION['test_microsite']["urls"] or MKTG_URL_LINK_MAP,
        # so web certificate will use CertificateHtmlViewConfiguration url.
        self.assertContains(
            response,
            configuration['microsites']['testmicrosite']['company_privacy_url'],
        )
        # TOS_AND_HONOR is not present in MICROSITE_CONFIGURATION['test_microsite']["urls"] or MKTG_URL_LINK_MAP,
        # so web certificate will use CertificateHtmlViewConfiguration url.
        self.assertContains(
            response,
            configuration['microsites']['testmicrosite']['company_tos_url'],
        )
