# -*- coding: utf-8 -*-
"""Tests for certificates views. """


import datetime
import json
from collections import OrderedDict
from uuid import uuid4

import ddt
import six
from django.conf import settings
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch
from urllib.parse import urlencode

from common.djangoapps.course_modes.models import CourseMode
from edx_toggles.toggles import WaffleSwitch
from edx_toggles.toggles.testutils import override_waffle_switch
from lms.djangoapps.badges.events.course_complete import get_completion_badge
from lms.djangoapps.badges.tests.factories import (
    BadgeAssertionFactory,
    BadgeClassFactory,
    CourseCompleteImageConfigurationFactory
)
from lms.djangoapps.certificates.api import get_certificate_url
from lms.djangoapps.certificates.models import (
    CertificateGenerationCourseSetting,
    CertificateHtmlViewConfiguration,
    CertificateSocialNetworks,
    CertificateStatuses,
    CertificateTemplate,
    CertificateTemplateAsset,
    GeneratedCertificate
)
from lms.djangoapps.certificates.tests.factories import (
    CertificateHtmlViewConfigurationFactory,
    GeneratedCertificateFactory,
    LinkedInAddToProfileConfigurationFactory
)
from lms.djangoapps.grades.tests.utils import mock_passing_grade
from openedx.core.djangoapps.certificates.config import waffle
from openedx.core.djangoapps.dark_lang.models import DarkLangConfig
from openedx.core.djangoapps.site_configuration.tests.test_util import (
    with_site_configuration,
    with_site_configuration_context
)
from openedx.core.djangolib.js_utils import js_escaped_string
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.core.lib.tests.assertions.events import assert_event_matches
from common.djangoapps.student.roles import CourseStaffRole
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from common.djangoapps.track.tests import EventTrackingTestCase
from common.djangoapps.util import organizations_helpers as organizations_api
from common.djangoapps.util.date_utils import strftime_localized
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

AUTO_CERTIFICATE_GENERATION_SWITCH = WaffleSwitch(waffle.waffle(), waffle.AUTO_CERTIFICATE_GENERATION)
FEATURES_WITH_CERTS_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_ENABLED['CERTIFICATES_HTML_VIEW'] = True
FEATURES_WITH_BADGES_ENABLED = FEATURES_WITH_CERTS_ENABLED.copy()
FEATURES_WITH_BADGES_ENABLED['ENABLE_OPENBADGES'] = True

FEATURES_WITH_CERTS_DISABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_DISABLED['CERTIFICATES_HTML_VIEW'] = False

FEATURES_WITH_CUSTOM_CERTS_ENABLED = {
    "CUSTOM_CERTIFICATE_TEMPLATES_ENABLED": True
}
FEATURES_WITH_CUSTOM_CERTS_ENABLED.update(FEATURES_WITH_CERTS_ENABLED)


class CommonCertificatesTestCase(ModuleStoreTestCase):
    """
    Common setUp and utility methods for Certificate tests
    """

    ENABLED_SIGNALS = ['course_published']

    def setUp(self):
        super(CommonCertificatesTestCase, self).setUp()
        self.client = Client()
        self.course = CourseFactory.create(
            org='testorg',
            number='run1',
            display_name='refundable course',
            certificate_available_date=datetime.datetime.today() - datetime.timedelta(days=1),
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
        self.linkedin_url = 'https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&{params}'

        self.cert = GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course_id,
            download_uuid=uuid4().hex,
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
        CourseCompleteImageConfigurationFactory.create()

    def _add_course_certificates(self, count=1, signatory_count=0, is_active=True):
        """
        Create certificate for the course.
        """
        signatories = [
            {
                'name': 'Signatory_Name ' + str(i),
                'title': 'Signatory_Title ' + str(i),
                'organization': 'Signatory_Organization ' + str(i),
                'signature_image_path': u'/static/certificates/images/demo-sig{}.png'.format(i),
                'id': i
            } for i in range(signatory_count)

        ]

        certificates = [
            {
                'id': i,
                'name': 'Name ' + str(i),
                'description': 'Description ' + str(i),
                'course_title': 'course_title_' + str(i),
                'org_logo_path': u'/t4x/orgX/testX/asset/org-logo-{}.png'.format(i),
                'signatories': signatories,
                'version': 1,
                'is_active': is_active
            } for i in range(count)
        ]

        self.course.certificates = {'certificates': certificates}
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)

    def _create_custom_template(self, org_id=None, mode=None, course_key=None, language=None):
        """
        Creates a custom certificate template entry in DB.
        """
        template_html = u"""
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
            is_active=True,
            language=language
        )
        template.save()

    def _create_custom_named_template(self, template_name, org_id=None, mode=None, course_key=None, language=None):
        """
        Creates a custom certificate template entry in DB.
        """
        template_html = u"""
            <%namespace name='static' file='static_content.html'/>
            <html>
            <body>
                lang: ${LANGUAGE_CODE}
                course name: """ + template_name + u"""
                mode: ${course_mode}
                ${accomplishment_copy_course_description}
                ${twitter_url}
                <img class="custom-logo" src="${static.certificate_asset_url('custom-logo')}" />
            </body>
            </html>
        """
        template = CertificateTemplate(
            name=template_name,
            template=template_html,
            organization_id=org_id,
            course_key=course_key,
            mode=mode,
            is_active=True,
            language=language
        )
        template.save()

    def _create_custom_template_with_hours_of_effort(self, org_id=None, mode=None, course_key=None, language=None):
        """
        Creates a custom certificate template entry in DB that includes hours of effort.
        """
        template_html = u"""
            <%namespace name='static' file='static_content.html'/>
            <html>
            <body>
                lang: ${LANGUAGE_CODE}
                course name: ${accomplishment_copy_course_name}
                mode: ${course_mode}
                % if hours_of_effort:
                    hours of effort: ${hours_of_effort}
                % endif
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
            is_active=True,
            language=language
        )
        template.save()


@ddt.ddt
class CertificatesViewsTests(CommonCertificatesTestCase, CacheIsolationTestCase):
    """
    Tests for the certificates web/html views
    """

    def setUp(self):
        super(CertificatesViewsTests, self).setUp()
        self.mock_course_run_details = {
            'content_language': 'en',
            'weeks_to_complete': '4',
            'max_effort': '10'
        }

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_linkedin_share_url(self):
        """
        Test: LinkedIn share URL.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(course_id=self.course.id, uuid=self.cert.verify_uuid)
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        params = {
            'name': '{platform_name} Honor Code Certificate for {course_name}'.format(
                platform_name=settings.PLATFORM_NAME, course_name=self.course.display_name,
            ).encode('utf-8'),
            'certUrl': self.request.build_absolute_uri(test_url),
            # default value from the LinkedInAddToProfileConfigurationFactory company_identifier
            'organizationId': 1337,
            'certId': self.cert.verify_uuid,
            'issueYear': self.cert.created_date.year,
            'issueMonth': self.cert.created_date.month,
        }
        self.assertContains(
            response,
            js_escaped_string(self.linkedin_url.format(params=urlencode(params))),
        )

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    @with_site_configuration(
        configuration={
            'platform_name': 'My Platform Site', 'LINKEDIN_COMPANY_ID': 2448,
        },
    )
    def test_linkedin_share_url_site(self):
        """
        Test: LinkedIn share URL should be visible when called from within a site.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(course_id=self.cert.course_id, uuid=self.cert.verify_uuid)
        response = self.client.get(test_url, HTTP_HOST='test.localhost')
        self.assertEqual(response.status_code, 200)
        # the linkedIn share URL with appropriate parameters should be present
        params = {
            'name': 'My Platform Site Honor Code Certificate for {course_name}'.format(
                course_name=self.course.display_name,
            ).encode('utf-8'),
            'certUrl': 'http://test.localhost' + test_url,
            'organizationId': 2448,
            'certId': self.cert.verify_uuid,
            'issueYear': self.cert.created_date.year,
            'issueMonth': self.cert.created_date.month,
        }
        self.assertContains(
            response,
            js_escaped_string(self.linkedin_url.format(params=urlencode(params))),
        )

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    @patch.dict("django.conf.settings.SOCIAL_SHARING_SETTINGS", {"CERTIFICATE_FACEBOOK": True})
    @with_site_configuration(
        configuration={'FACEBOOK_APP_ID': 'test_facebook_my_site'},
    )
    def test_facebook_share_url_site(self):
        """
        Test: Facebook share URL should be visible when web cert called from within a white label
        site and it should use white label site's FACEBOOK_APP_ID.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(course_id=self.cert.course_id, uuid=self.cert.verify_uuid)
        response = self.client.get(test_url, HTTP_HOST='test.localhost')
        self.assertContains(response, "Post on Facebook")
        self.assertContains(response, 'test_facebook_my_site')

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    @ddt.data(
        (False, False, False),
        (False, False, True),
        (False, True, True),
        (True, True, True),
        (True, True, False),
    )
    @ddt.unpack
    def test_social_sharing_availability_site(self, facebook_sharing, twitter_sharing, linkedin_sharing):
        """
        Test: Facebook, Twitter and LinkedIn sharing availability for sites.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(course_id=self.cert.course_id, uuid=self.cert.verify_uuid)
        social_sharing_settings = dict(
            CERTIFICATE_FACEBOOK=facebook_sharing,
            CERTIFICATE_TWITTER=twitter_sharing,
            CERTIFICATE_LINKEDIN=linkedin_sharing,
        )
        with with_site_configuration_context(
            configuration={
                'platform_name': 'My Platform Site',
                'SOCIAL_SHARING_SETTINGS': social_sharing_settings,
            },
        ):
            response = self.client.get(test_url, HTTP_HOST='test.localhost')
            self.assertEqual(response.status_code, 200)
            self.assertEqual("Post on Facebook" in response.content.decode('utf-8'), facebook_sharing)
            self.assertEqual("Share on Twitter" in response.content.decode('utf-8'), twitter_sharing)
            self.assertEqual("Add to LinkedIn Profile" in response.content.decode('utf-8'), linkedin_sharing)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_facebook_default_text_site(self):
        """
        Test: Facebook sharing default text for sites.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(course_id=self.cert.course_id, uuid=self.cert.verify_uuid)
        facebook_text = "Facebook text on Test Site"
        social_sharing_settings = dict(
            CERTIFICATE_FACEBOOK=True,
            CERTIFICATE_FACEBOOK_TEXT=facebook_text,
        )
        with with_site_configuration_context(
            configuration={
                'SOCIAL_SHARING_SETTINGS': social_sharing_settings,
            },
        ):
            response = self.client.get(test_url, HTTP_HOST='test.localhost')
            self.assertContains(response, facebook_text)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_twitter_default_text_site(self):
        """
        Test: Twitter sharing default text for sites.
        """
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(course_id=self.cert.course_id, uuid=self.cert.verify_uuid)
        twitter_text = "Twitter text on Test Site"
        social_sharing_settings = dict(
            CERTIFICATE_TWITTER=True,
            CERTIFICATE_TWITTER_TEXT=twitter_text,
        )
        with with_site_configuration_context(
            configuration={
                'SOCIAL_SHARING_SETTINGS': social_sharing_settings,
            },
        ):
            response = self.client.get(test_url, HTTP_HOST='test.localhost')
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
        organizations_api.add_organization_course(organization_data=test_org, course_id=six.text_type(self.course.id))
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url)
        self.assertContains(
            response,
            'a course of study offered by test_organization, an online learning initiative of test organization',
        )
        self.assertNotContains(response, 'a course of study offered by testorg')
        self.assertContains(response, u'<title>test_organization {} Certificate |'.format(self.course.number, ))
        self.assertContains(response, 'logo_test1.png')

    @ddt.data(True, False)
    @patch('lms.djangoapps.certificates.views.webview.get_completion_badge')
    def test_fetch_badge_info(self, issue_badges, mock_get_completion_badge):
        """
        Test: Fetch badge class info if badges are enabled.
        """
        if issue_badges:
            features = FEATURES_WITH_BADGES_ENABLED
        else:
            features = FEATURES_WITH_CERTS_ENABLED
        with override_settings(FEATURES=features):
            badge_class = BadgeClassFactory(course_id=self.course_id, mode=self.cert.mode)
            mock_get_completion_badge.return_value = badge_class

            self._add_course_certificates(count=1, signatory_count=1, is_active=True)
            test_url = get_certificate_url(user_id=self.user.id, course_id=self.cert.course_id,
                                           uuid=self.cert.verify_uuid)
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)

        if issue_badges:
            mock_get_completion_badge.assert_called()
        else:
            mock_get_completion_badge.assert_not_called()

    @override_settings(FEATURES=FEATURES_WITH_BADGES_ENABLED)
    @patch.dict("django.conf.settings.SOCIAL_SHARING_SETTINGS", {
        "CERTIFICATE_TWITTER": True,
        "CERTIFICATE_FACEBOOK": True,
    })
    @with_site_configuration(
        configuration=dict(
            platform_name='My Platform Site',
            SITE_NAME='test_site.localhost',
            urls=dict(
                ABOUT='http://www.test-site.org/about-us',
            ),
        ),
    )
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
        organizations_api.add_organization_course(organization_data=test_org, course_id=six.text_type(self.course.id))
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        badge_class = get_completion_badge(course_id=self.course_id, user=self.user)
        BadgeAssertionFactory.create(
            user=self.user, badge_class=badge_class,
        )
        self.course.cert_html_view_overrides = {
            "logo_src": "/static/certificates/images/course_override_logo.png"
        }

        self.course.save()
        self.store.update_item(self.course, self.user.id)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url, HTTP_HOST='test.localhost')

        # Test an item from basic info
        self.assertContains(response, 'Terms of Service &amp; Honor Code')
        self.assertContains(response, 'Certificate ID Number')
        # Test an item from html cert configuration
        self.assertContains(response, '<a class="logo" href="http://test_site.localhost">')
        # Test an item from course info
        self.assertContains(response, 'course_title_0')
        # Test an item from user info
        self.assertContains(response, u"{fullname}, you earned a certificate!".format(fullname=self.user.profile.name))
        # Test an item from social info
        self.assertContains(response, "Post on Facebook")
        self.assertContains(response, "Share on Twitter")
        # Test an item from certificate/org info
        self.assertContains(
            response,
            u"a course of study offered by {partner_short_name}, "
            "an online learning initiative of "
            "{partner_long_name}.".format(
                partner_short_name=short_org_name,
                partner_long_name=long_org_name,
            ),
        )
        # Test item from badge info
        self.assertContains(response, "Add to Mozilla Backpack")
        # Test item from site configuration
        self.assertContains(response, "http://www.test-site.org/about-us")
        # Test course overrides
        self.assertContains(response, "/static/certificates/images/course_override_logo.png")

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_valid_certificate(self):
        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url)
        self.assertContains(response, str(self.cert.verify_uuid))

        # Hit any "verified" mode-specific branches
        self.cert.mode = 'verified'
        self.cert.save()
        response = self.client.get(test_url)
        self.assertContains(response, str(self.cert.verify_uuid))

        # Hit any 'xseries' mode-specific branches
        self.cert.mode = 'xseries'
        self.cert.save()
        response = self.client.get(test_url)
        self.assertContains(response, str(self.cert.verify_uuid))

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_certificate_only_for_downloadable_status(self):
        """
        Tests taht Certificate HTML Web View returns Certificate only if certificate status is 'downloadable',
        for other statuses it should return "Invalid Certificate".
        """
        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )

        # Validate certificate
        response = self.client.get(test_url)
        self.assertContains(response, str(self.cert.verify_uuid))

        # Change status to 'generating' and validate that Certificate Web View returns "Invalid Certificate"
        self.cert.status = CertificateStatuses.generating
        self.cert.save()
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 404)

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
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url)
        if eligible_for_certificate:
            self.assertContains(response, str(self.cert.verify_uuid))
        else:
            self.assertEqual(response.status_code, 404)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_html_view_returns_404_for_invalid_certificate(self):
        """
        Tests that Certificate HTML Web View successfully retrieves certificate only
        if the certificate is not invalidated otherwise returns 404
        """
        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )

        # Validate certificate
        response = self.client.get(test_url)
        self.assertContains(response, str(self.cert.verify_uuid))

        # invalidate certificate and verify that "Cannot Find Certificate" is returned
        self.cert.invalidate()
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 404)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_html_lang_attribute_is_dynamic_for_certificate_html_view(self):
        """
        Tests that Certificate HTML Web View's lang attribute is based on user language.
        """
        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )

        user_language = 'fr'
        self.client.cookies[settings.LANGUAGE_COOKIE] = user_language
        response = self.client.get(test_url)
        self.assertContains(response, '<html class="no-js" lang="fr">')

        user_language = 'ar'
        self.client.cookies[settings.LANGUAGE_COOKIE] = user_language
        response = self.client.get(test_url)
        self.assertContains(response, '<html class="no-js" lang="ar">')

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_html_view_for_non_viewable_certificate_and_for_student_user(self):
        """
        Tests that Certificate HTML Web View returns "Cannot Find Certificate" if certificate is not viewable yet.
        """
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
        self.course.certificate_available_date = datetime.datetime.today() + datetime.timedelta(days=1)
        self.course.save()
        self.store.update_item(self.course, self.user.id)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url)
        self.assertContains(response, "Invalid Certificate")
        self.assertContains(response, "Cannot Find Certificate")
        self.assertContains(response, "We cannot find a certificate with this URL or ID number.")

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_with_valid_signatories(self):
        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )

        response = self.client.get(test_url)
        self.assertContains(response, 'course_title_0')
        self.assertContains(response, 'Signatory_Name 0')
        self.assertContains(response, 'Signatory_Title 0')
        self.assertContains(response, 'Signatory_Organization 0')
        self.assertContains(response, '/static/certificates/images/demo-sig0.png')

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
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )

        response = self.client.get(test_url)
        self.assertNotContains(response, 'test_course_title_0')
        self.assertContains(response, 'refundable course')

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
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )

        self.course.display_coursenumber = "overridden_number"
        self.course.display_organization = "overridden_org"
        self.store.update_item(self.course, self.user.id)

        response = self.client.get(test_url)
        self.assertContains(response, 'overridden_number')
        self.assertContains(response, 'overridden_org')

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
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url)
        # make sure response html has only one organization logo container for edX
        self.assertContains(response, "<li class=\"wrapper-organization\">", 1)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_without_signatories(self):
        self._add_course_certificates(count=1, signatory_count=0)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url)
        self.assertNotContains(response, 'Signatory_Name 0')
        self.assertNotContains(response, 'Signatory_Title 0')

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_is_html_escaped(self):
        test_certificates = [
            {
                'id': 0,
                'name': 'Certificate Name',
                'description': '<script>Description</script>',
                'course_title': '<script>course_title</script>',
                'org_logo_path': '/t4x/orgX/testX/asset/org-logo-1.png',
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
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url)
        self.assertNotContains(response, '<script>')
        self.assertContains(response, '&lt;script&gt;course_title&lt;/script&gt;')

    @override_settings(FEATURES=FEATURES_WITH_CERTS_DISABLED)
    def test_render_html_view_disabled_feature_flag_returns_static_url(self):
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        self.assertIn(str(self.cert.download_url), test_url)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_course(self):
        test_url = "/certificates/user/{user_id}/course/{course_id}".format(
            user_id=self.user.id,
            course_id="missing/course/key"
        )
        response = self.client.get(test_url)
        self.assertContains(response, 'invalid')

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_user_certificate(self):
        self._add_course_certificates(count=1, signatory_count=0)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        self.cert.delete()
        self.assertListEqual(list(GeneratedCertificate.eligible_certificates.all()), [])

        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 404)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED, PLATFORM_NAME=u'Űńíćődé Űńívéŕśítӳ')
    def test_render_html_view_with_unicode_platform_name(self):
        self._add_course_certificates(count=1, signatory_count=0)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_user_id_cert_url_not_supported(self):
        """
        tests the user id based certificate url is no longer supported
        """
        test_url = reverse(
            'certificates:unsupported_url', kwargs={'user_id': self.user.id, 'course_id': self.course_id}
        )
        response = self.client.get(test_url + '?preview=honor')
        # accessing certificate web view in preview mode without
        # staff or instructor access should show invalid certificate
        self.assertContains(response, 'URL Not Supported')

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_with_preview_mode(self):
        """
        test certificate web view should render properly along with its signatories information when accessing it in
        preview mode only for the staff users. Either the certificate is marked active or not.
        """
        self._add_course_certificates(count=1, signatory_count=2)
        self.user.is_staff = True
        self.user.save()
        test_url = reverse('certificates:preview_cert', kwargs={'course_id': self.course_id})
        response = self.client.get(test_url + '?preview=honor')

        self.assertNotContains(response, self.course.display_name.encode('utf-8'))
        self.assertContains(response, 'course_title_0')
        self.assertContains(response, 'Signatory_Title 0')

        # mark certificate inactive but accessing in preview mode.
        self._add_course_certificates(count=1, signatory_count=2, is_active=False)
        response = self.client.get(test_url + '?preview=honor')
        self.assertNotContains(response, self.course.display_name.encode('utf-8'))
        self.assertContains(response, 'course_title_0')
        self.assertContains(response, 'Signatory_Title 0')

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
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        # user has already has certificate generated for 'honor' mode
        # so let's try to preview in 'verified' mode.
        response = self.client.get(test_url + '?preview=verified')
        self.assertNotContains(response, self.course.display_name.encode('utf-8'))
        self.assertContains(response, 'course_title_0')
        self.assertContains(response, 'Signatory_Title 0')

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    @ddt.data(
        (-2, True),
        (-2, False)
    )
    @ddt.unpack
    def test_html_view_certificate_available_date_for_instructor_paced_courses(self, cert_avail_delta, self_paced):
        """
        test certificate web view should display the certificate available date
        as the issued date for instructor-paced courses
        """
        self.course.self_paced = self_paced
        today = datetime.datetime.utcnow()
        self.course.certificate_available_date = today + datetime.timedelta(cert_avail_delta)
        self.store.update_item(self.course, self.user.id)
        self._add_course_certificates(count=1, signatory_count=1, is_active=True)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )

        if self_paced or self.course.certificate_available_date > today:
            expected_date = today
        else:
            expected_date = self.course.certificate_available_date
        with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
            response = self.client.get(test_url)
        date = u'{month} {day}, {year}'.format(
            month=strftime_localized(expected_date, "%B"),
            day=expected_date.day,
            year=expected_date.year
        )
        self.assertContains(response, date)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_html_view_invalid_certificate_configuration(self):
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url)
        self.assertContains(response, "Invalid Certificate")

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_render_500_view_invalid_certificate_configuration(self):
        self._add_course_certificates(count=1, signatory_count=2)
        CertificateHtmlViewConfiguration.objects.all().update(enabled=False)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url + "?preview=honor")
        self.assertContains(response, "Invalid Certificate Configuration")

        # Verify that Exception is raised when certificate is not in the preview mode
        with self.assertRaises(Exception):
            self.client.get(test_url)

    @override_settings(FEATURES=FEATURES_WITH_CERTS_DISABLED)
    def test_request_certificate_without_passing(self):
        self.cert.status = CertificateStatuses.unavailable
        self.cert.save()
        request_certificate_url = reverse('request_certificate')
        response = self.client.post(request_certificate_url, {'course_id': six.text_type(self.course.id)})
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(CertificateStatuses.notpassing, response_json['add_status'])

    @override_settings(FEATURES=FEATURES_WITH_CERTS_DISABLED)
    @override_settings(CERT_QUEUE='test-queue')
    def test_request_certificate_after_passing(self):
        self.cert.status = CertificateStatuses.unavailable
        self.cert.save()
        request_certificate_url = reverse('request_certificate')
        with patch('capa.xqueue_interface.XQueueInterface.send_to_queue') as mock_queue:
            mock_queue.return_value = (0, "Successfully queued")
            with mock_passing_grade():
                response = self.client.post(request_certificate_url, {'course_id': six.text_type(self.course.id)})
                self.assertEqual(response.status_code, 200)
                response_json = json.loads(response.content.decode('utf-8'))
                self.assertEqual(CertificateStatuses.generating, response_json['add_status'])

    #TEMPLATES WITHOUT LANGUAGE TESTS
    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    @override_settings(LANGUAGE_CODE='fr')
    @patch('lms.djangoapps.certificates.views.webview.get_course_run_details')
    def test_certificate_custom_template_with_org_mode_and_course_key(self, mock_get_course_run_details):
        """
        Tests custom template search and rendering.
        This test should check template matching when org={org}, course={course}, mode={mode}.
        """
        mock_get_course_run_details.return_value = self.mock_course_run_details
        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_named_template(
            'test_template_1_course', org_id=1, mode='honor', course_key=six.text_type(self.course.id),
        )
        self._create_custom_named_template(
            'test_template_2_course', org_id=1, mode='verified', course_key=six.text_type(self.course.id),
        )
        self._create_custom_named_template('test_template_3_course', org_id=2, mode='honor')
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )

        with patch('lms.djangoapps.certificates.api.get_course_organization_id') as mock_get_org_id:
            mock_get_org_id.side_effect = [1, 2]
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'lang: fr')
            self.assertContains(response, 'course name: test_template_1_course')
            # test with second organization template
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'lang: fr')
            self.assertContains(response, 'course name: test_template_3_course')

    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    @patch('lms.djangoapps.certificates.views.webview.get_course_run_details')
    def test_certificate_custom_template_with_org_and_mode(self, mock_get_course_run_details):
        """
        Tests custom template search if no template matches course_key, but a template does
        match org and mode.
        This test should check template matching when org={org}, course=Null, mode={mode}.
        """
        mock_get_course_run_details.return_value = self.mock_course_run_details
        othercourse = CourseFactory.create(
            org='cstX', number='cst_22', display_name='custom template course'
        )

        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_named_template('test_template_1_course', org_id=1, mode='honor')  # Correct template
        self._create_custom_named_template(  # wrong course key
            'test_template_2_course',
            org_id=1,
            mode='honor',
            course_key=six.text_type(othercourse.id)
        )
        self._create_custom_named_template('test_template_3_course', org_id=1, mode='verified')  # wrong mode
        self._create_custom_named_template('test_template_4_course', org_id=2, mode='honor')  # wrong org
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )

        with patch('lms.djangoapps.certificates.api.get_course_organization_id') as mock_get_org_id:
            mock_get_org_id.side_effect = [1]
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'course name: test_template_1_course')

    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    @patch('lms.djangoapps.certificates.views.webview.get_course_run_details')
    def test_certificate_custom_template_with_org(self, mock_get_course_run_details):
        """
        Tests custom template search when we have a single template for a organization.
        This test should check template matching when org={org}, course=Null, mode=null.
        """
        mock_get_course_run_details.return_value = self.mock_course_run_details
        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_named_template('test_template_1_course', org_id=1, mode=None)  # Correct template
        self._create_custom_named_template('test_template_2_course', org_id=1, mode='verified')  # wrong mode
        self._create_custom_named_template('test_template_3_course', org_id=2, mode=None)  # wrong org
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )

        with patch('lms.djangoapps.certificates.api.get_course_organization_id') as mock_get_org_id:
            mock_get_org_id.side_effect = [1]
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'course name: test_template_1_course')

    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    @patch('lms.djangoapps.certificates.views.webview.get_course_run_details')
    def test_certificate_custom_template_with_mode(self, mock_get_course_run_details):
        """
        Tests custom template search if we have a single template for a course mode.
        This test should check template matching when org=null, course=Null, mode={mode}.
        """
        mock_get_course_run_details.return_value = self.mock_course_run_details
        mode = 'honor'
        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_named_template('test_template_1_course', org_id=None, mode=mode)  # Correct template
        self._create_custom_named_template('test_template_2_course', org_id=None, mode='verified')  # wrong mode
        self._create_custom_named_template('test_template_3_course', org_id=2, mode=mode)  # wrong org
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )

        with patch('lms.djangoapps.certificates.api.get_course_organization_id') as mock_get_org_id:
            mock_get_org_id.return_value = None
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, u'mode: {}'.format(mode))
            self.assertContains(response, 'course name: test_template_1_course')

    ## Templates With Language tests
    #1
    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    @override_settings(LANGUAGE_CODE='fr')
    @patch('lms.djangoapps.certificates.views.webview.get_course_run_details')
    @patch('lms.djangoapps.certificates.api.get_course_organization_id')
    def test_certificate_custom_language_template_with_org_mode_and_course_key(
            self,
            mock_get_org_id,
            mock_get_course_run_details,
    ):
        """
        Tests custom template search and rendering.
        This test should check template matching when org={org}, course={course}, mode={mode}.
        """
        DarkLangConfig(released_languages='es-419, fr', changed_by=self.user, enabled=True).save()

        right_language = 'es'
        wrong_language = 'fr'
        mock_get_org_id.return_value = 1
        course_run_details = self.mock_course_run_details
        course_run_details.update({'content_language': 'es'})
        mock_get_course_run_details.return_value = course_run_details

        CertificateGenerationCourseSetting.objects.update_or_create(
            course_key=self.course.id,
            defaults={
                'language_specific_templates_enabled': True
            }
        )

        self._add_course_certificates(count=1, signatory_count=2)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        #create a org_mode_and_coursekey template language=null
        self._create_custom_named_template(
            'test_null_lang_template', org_id=1, mode='honor', course_key=six.text_type(self.course.id), language=None,
        )
        #verify return template lang = null
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_null_lang_template')

        #create a org_mode_and_coursekey template language=wrong_language
        self._create_custom_named_template(
            'test_wrong_lang_template',
            org_id=1,
            mode='honor',
            course_key=six.text_type(self.course.id),
            language=wrong_language,
        )
        #verify returns null lang template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_null_lang_template')

        #create an org_mode_and_coursekey template language=''
        self._create_custom_named_template(
            'test_all_languages_template',
            org_id=1,
            mode='honor',
            course_key=six.text_type(self.course.id),
            language='',
        )
        #verify returns null lang template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_all_languages_template')

        #create a org_mode_and_coursekey template language=lang
        self._create_custom_named_template(
            'test_right_lang_template',
            org_id=1,
            mode='honor',
            course_key=six.text_type(self.course.id),
            language=right_language,
        )
        # verify return right_language template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_right_lang_template')

    #2
    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    @patch('lms.djangoapps.certificates.views.webview.get_course_run_details')
    @patch('lms.djangoapps.certificates.api.get_course_organization_id')
    def test_certificate_custom_language_template_with_org_and_mode(self, mock_get_org_id, mock_get_course_run_details):
        """
        Tests custom template search if no template matches course_key, but a template does
        match org and mode.
        This test should check template matching when org={org}, course=Null, mode={mode}.
        """
        DarkLangConfig(released_languages='es-419, fr', changed_by=self.user, enabled=True).save()

        right_language = 'es'
        wrong_language = 'fr'
        mock_get_org_id.return_value = 1
        course_run_details = self.mock_course_run_details
        course_run_details.update({'content_language': 'es'})
        mock_get_course_run_details.return_value = course_run_details
        CertificateGenerationCourseSetting.objects.update_or_create(
            course_key=self.course.id,
            defaults={
                'language_specific_templates_enabled': True
            }
        )

        self._add_course_certificates(count=1, signatory_count=2)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        #create a org and mode template language=null
        self._create_custom_named_template('test_null_lang_template', org_id=1, mode='honor', language=None)
        #verify return template lang = null
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_null_lang_template')

        #create a org and mode template language=wrong_language
        self._create_custom_named_template('test_wrong_lang_template', org_id=1, mode='honor', language=wrong_language)
        #verify returns null lang template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_null_lang_template')

        #create an org and mode template language=''
        self._create_custom_named_template('test_all_languages_template', org_id=1, mode='honor', language='')
        #verify returns All Languages template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_all_languages_template')

        #create a org and mode template language=lang
        self._create_custom_named_template('test_right_lang_template', org_id=1, mode='honor', language=right_language)
        # verify return right_language template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_right_lang_template')

    #3
    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    @patch('lms.djangoapps.certificates.views.webview.get_course_run_details')
    @patch('lms.djangoapps.certificates.api.get_course_organization_id')
    def test_certificate_custom_language_template_with_org(self, mock_get_org_id, mock_get_course_run_details):
        """
        Tests custom template search when we have a single template for a organization.
        This test should check template matching when org={org}, course=Null, mode=null.
        """
        DarkLangConfig(released_languages='es-419, fr', changed_by=self.user, enabled=True).save()

        right_language = 'es'
        wrong_language = 'fr'
        mock_get_org_id.return_value = 1
        course_run_details = self.mock_course_run_details
        course_run_details.update({'content_language': 'es'})
        mock_get_course_run_details.return_value = course_run_details
        CertificateGenerationCourseSetting.objects.update_or_create(
            course_key=self.course.id,
            defaults={
                'language_specific_templates_enabled': True
            }
        )

        self._add_course_certificates(count=1, signatory_count=2)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        #create a org template language=null
        self._create_custom_named_template('test_null_lang_template', org_id=1, language=None)
        #verify return template lang = null
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_null_lang_template')

        #create a org template language=wrong_language
        self._create_custom_named_template('test_wrong_lang_template', org_id=1, language=wrong_language)
        #verify returns null lang template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_null_lang_template')

        #create an org template language=''
        self._create_custom_named_template('test_all_languages_template', org_id=1, language='')
        #verify returns All Languages template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_all_languages_template')

        #create a org template language=lang
        self._create_custom_named_template('test_right_lang_template', org_id=1, language=right_language)
        # verify return right_language template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_right_lang_template')

    #4
    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    @patch('lms.djangoapps.certificates.views.webview.get_course_run_details')
    @patch('lms.djangoapps.certificates.api.get_course_organization_id')
    def test_certificate_custom_language_template_with_mode(self, mock_get_org_id, mock_get_course_run_details):
        """
        Tests custom template search if we have a single template for a course mode.
        This test should check template matching when org=null, course=Null, mode={mode}.
        """
        DarkLangConfig(released_languages='es-419, fr', changed_by=self.user, enabled=True).save()

        right_language = 'es'
        wrong_language = 'fr'
        mock_get_org_id.return_value = 1
        course_run_details = self.mock_course_run_details
        course_run_details.update({'content_language': 'es'})
        mock_get_course_run_details.return_value = course_run_details
        CertificateGenerationCourseSetting.objects.update_or_create(
            course_key=self.course.id,
            defaults={
                'language_specific_templates_enabled': True
            }
        )

        self._add_course_certificates(count=1, signatory_count=2)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        #create a mode template language=null
        self._create_custom_named_template('test_null_lang_template', mode='honor', language=None)
        #verify return template with lang = null
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_null_lang_template')

        #create a mode template language=wrong_language
        self._create_custom_named_template('test_wrong_lang_template', mode='honor', language=wrong_language)
        #verify returns null lang template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_null_lang_template')

        #create a mode template language=''
        self._create_custom_named_template('test_all_languages_template', mode='honor', language='')
        #verify returns All Languages template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_all_languages_template')

        #create a mode template language=lang
        self._create_custom_named_template('test_right_lang_template', mode='honor', language=right_language)
        # verify return right_language template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_right_lang_template')

    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    @patch('lms.djangoapps.certificates.views.webview.get_course_run_details')
    @patch('lms.djangoapps.certificates.api.get_course_organization_id')
    def test_certificate_custom_language_template_with_locale_language_from_catalogue(
            self,
            mock_get_org_id,
            mock_get_course_run_details,
    ):
        """
        Tests custom template search if we have a single template for a course mode.
        This test should check template matching when org=null, course=Null, mode={mode}.
        """
        DarkLangConfig(released_languages='es-419, fr', changed_by=self.user, enabled=True).save()

        right_language = 'es'
        wrong_language = 'fr'
        mock_get_org_id.return_value = 1
        course_run_details = self.mock_course_run_details
        course_run_details.update({'content_language': 'es-419'})
        mock_get_course_run_details.return_value = course_run_details
        CertificateGenerationCourseSetting.objects.update_or_create(
            course_key=self.course.id,
            defaults={
                'language_specific_templates_enabled': True
            }
        )

        self._add_course_certificates(count=1, signatory_count=2)

        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        #create a mode template language=null
        self._create_custom_named_template('test_null_lang_template', org_id=1, mode='honor', language=None)
        #verify return template with lang = null
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_null_lang_template')

        #create a mode template language=wrong_language
        self._create_custom_named_template('test_wrong_lang_template', org_id=1, mode='honor', language=wrong_language)
        #verify returns null lang template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_null_lang_template')

        #create a mode template language=''
        self._create_custom_named_template('test_all_languages_template', org_id=1, mode='honor', language='')
        #verify returns All Languages template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_all_languages_template')

        #create a mode template language=lang
        self._create_custom_named_template('test_right_lang_template', org_id=1, mode='honor', language=right_language)
        # verify return right_language template
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'course name: test_right_lang_template')

    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    @ddt.data(True, False)
    @patch('lms.djangoapps.certificates.views.webview.get_course_run_details')
    @patch('lms.djangoapps.certificates.api.get_course_organization_id')
    def test_certificate_custom_template_with_hours_of_effort(
            self,
            include_effort,
            mock_get_org_id,
            mock_get_course_run_details,
    ):
        """
        Tests custom template properly retrieves and calculates Hours of Effort when the feature is enabled
        """
        # mock the response data from Discovery that updates the context for template lookup and rendering
        mock_get_course_run_details.return_value = self.mock_course_run_details
        mock_get_org_id.return_value = 1
        CertificateGenerationCourseSetting.objects.update_or_create(
            course_key=self.course.id,
            defaults={
                'include_hours_of_effort': include_effort
            }
        )
        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_template_with_hours_of_effort(org_id=1, language=None)
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        if include_effort:
            self.assertContains(response, 'hours of effort: 40')
        else:
            self.assertNotContains(response, 'hours of effort')

    @ddt.data(True, False)
    @patch('lms.djangoapps.certificates.views.webview.get_course_run_details')
    def test_certificate_custom_template_with_unicode_data(self, custom_certs_enabled, mock_get_course_run_details):
        """
        Tests custom template renders properly with unicode data.
        """
        mock_get_course_run_details.return_value = self.mock_course_run_details
        mode = 'honor'
        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_template(mode=mode)
        with patch.dict("django.conf.settings.FEATURES", {
            "CERTIFICATES_HTML_VIEW": True,
            "CUSTOM_CERTIFICATE_TEMPLATES_ENABLED": custom_certs_enabled
        }):
            test_url = get_certificate_url(
                user_id=self.user.id,
                course_id=six.text_type(self.course.id),
                uuid=self.cert.verify_uuid
            )
            with patch.dict("django.conf.settings.SOCIAL_SHARING_SETTINGS", {
                "CERTIFICATE_TWITTER": True,
                "CERTIFICATE_TWITTER_TEXT": u"nền tảng học tập"
            }):
                with patch('django.http.HttpRequest.build_absolute_uri') as mock_abs_uri:
                    mock_abs_uri.return_value = '='.join(['http://localhost/?param', u'é'])
                    with patch('lms.djangoapps.certificates.api.get_course_organization_id') as mock_get_org_id:
                        mock_get_org_id.return_value = None
                        response = self.client.get(test_url)
                        self.assertEqual(response.status_code, 200)
                        if custom_certs_enabled:
                            self.assertContains(response, u'mode: {}'.format(mode))
                        else:
                            self.assertContains(response, "Tweet this Accomplishment")
                        self.assertContains(response, 'https://twitter.com/intent/tweet')

    @override_settings(FEATURES=FEATURES_WITH_CUSTOM_CERTS_ENABLED)
    @patch('lms.djangoapps.certificates.views.webview.get_course_run_details')
    def test_certificate_asset_by_slug(self, mock_get_course_run_details):
        """
        Tests certificate template asset display by slug using static.certificate_asset_url method.
        """
        mock_get_course_run_details.return_value = self.mock_course_run_details
        self._add_course_certificates(count=1, signatory_count=2)
        self._create_custom_template(mode='honor')
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )

        # render certificate without template asset
        with patch('lms.djangoapps.certificates.api.get_course_organization_id') as mock_get_org_id:
            mock_get_org_id.return_value = None
            response = self.client.get(test_url)
            self.assertContains(response, '<img class="custom-logo" src="" />')

        template_asset = CertificateTemplateAsset(
            description='custom logo',
            asset='certificate_template_assets/32/test_logo.png',
            asset_slug='custom-logo',
        )
        template_asset.save()

        # render certificate with template asset
        with patch('lms.djangoapps.certificates.api.get_course_organization_id') as mock_get_org_id:
            mock_get_org_id.return_value = None
            response = self.client.get(test_url)
            self.assertContains(
                response, u'<img class="custom-logo" src="{}certificate_template_assets/32/test_logo.png" />'.format(
                    settings.MEDIA_URL
                )
            )


class CertificateEventTests(CommonCertificatesTestCase, EventTrackingTestCase):
    """
    Test events emitted by certificate handling.
    """

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_certificate_evidence_event_emitted(self):
        self.client.logout()
        self._add_course_certificates(count=1, signatory_count=2)
        self.recreate_tracker()
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=six.text_type(self.course.id),
            uuid=self.cert.verify_uuid
        )
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)

        # There are two events being emitted in this flow.
        # One for page hit (due to the tracker in the middleware) and
        # one due to the certificate being visited.
        # We are interested in the second one.
        actual_event = self.get_event(1)

        self.assertEqual(actual_event['name'], 'edx.certificate.evidence_visited')
        assert_event_matches(
            {
                'user_id': self.user.id,
                'certificate_id': six.text_type(self.cert.verify_uuid),
                'enrollment_mode': self.cert.mode,
                'certificate_url': test_url,
                'course_id': six.text_type(self.course.id),
                'social_network': CertificateSocialNetworks.linkedin
            },
            actual_event['data']
        )

    @override_settings(FEATURES=FEATURES_WITH_CERTS_ENABLED)
    def test_evidence_event_sent(self):
        self._add_course_certificates(count=1, signatory_count=2)

        cert_url = get_certificate_url(
            user_id=self.user.id,
            course_id=self.course_id,
            uuid=self.cert.verify_uuid
        )
        test_url = '{}?evidence_visit=1'.format(cert_url)
        self.recreate_tracker()
        badge_class = get_completion_badge(self.course_id, self.user)
        assertion = BadgeAssertionFactory.create(
            user=self.user, badge_class=badge_class,
            backend='DummyBackend',
            image_url='http://www.example.com/image.png',
            assertion_url='http://www.example.com/assertion.json',
            data={
                'issuer': 'http://www.example.com/issuer.json',
            }
        )
        response = self.client.get(test_url)

        # There are two events being emitted in this flow.
        # One for page hit (due to the tracker in the middleware) and
        # one due to the certificate being visited.
        # We are interested in the second one.
        actual_event = self.get_event(1)

        self.assertEqual(response.status_code, 200)
        assert_event_matches(
            {
                'name': 'edx.badge.assertion.evidence_visited',
                'data': {
                    'course_id': 'testorg/run1/refundable_course',
                    'assertion_id': assertion.id,
                    'badge_generator': u'DummyBackend',
                    'badge_name': u'refundable course',
                    'issuing_component': u'',
                    'badge_slug': u'testorgrun1refundable_course_honor_432f164',
                    'assertion_json_url': 'http://www.example.com/assertion.json',
                    'assertion_image_url': 'http://www.example.com/image.png',
                    'user_id': self.user.id,
                    'issuer': 'http://www.example.com/issuer.json',
                    'enrollment_mode': 'honor',
                },
            },
            actual_event
        )
