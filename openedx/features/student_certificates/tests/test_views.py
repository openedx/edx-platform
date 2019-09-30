"""
This file contains the test cases for views of the student_certificates app
"""

from datetime import datetime, timedelta
from pyquery import PyQuery as pq
import pytz

from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import timezone
from django.db.models import signals
from django.contrib.sites.models import Site
from django.http import HttpRequest
from django.http import Http404
from django.test.utils import override_settings

import factory
import mock
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore import ModuleStoreEnum

from lms.djangoapps.onboarding.tests.factories import UserFactory
from certificates.models import GeneratedCertificate
from student.models import CourseEnrollment
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.factories import CourseFactory
from certificates.tests.factories import GeneratedCertificateFactory
from course_modes.tests.factories import CourseModeFactory
from openedx.core.djangoapps.theming.models import SiteTheme
from custom_settings.models import CustomSettings
from lms.djangoapps.onboarding.helpers import get_current_utc_date
from openedx.features.student_certificates.helpers import get_philu_certificate_social_context
from openedx.features.student_certificates.views import student_certificates, shared_student_achievements
from openedx.features.student_certificates.constants import TWITTER_META_TITLE_FMT, COURSE_URL_FMT
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class GenerateStudentCertificateViewsTestCase(SharedModuleStoreTestCase):
    """
        Tests for generating student course certificates.
    """
    CUSTOM_FEATURES = settings.FEATURES.copy()
    CUSTOM_FEATURES['CERTIFICATES_HTML_VIEW'] = True

    @classmethod
    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def setUpClass(cls):
        super(GenerateStudentCertificateViewsTestCase, cls).setUpClass()
        site = Site(domain='testserver', name='test')
        site.save()
        theme = SiteTheme(site=site, theme_dir_name='philu')
        theme.save()

        cls.download_url = '/certificate.pdf'
        cls.course = CourseFactory.create()
        cls.course.certificates_display_behavior = 'early_with_info'
        cls.username = 'test_user'
        cls.password = 'password'

        from openedx.features.course_card.tests.helpers import initialize_test_user
        cls.user = initialize_test_user(password=cls.password)
        cls.user.save()
        cls.course_settings = CustomSettings(id=cls.course.id, course_short_id=1, course_open_date=get_current_utc_date())
        cls.course_settings.save()

        CourseEnrollmentFactory.create(
            user=cls.user,
            course_id=cls.course.id,
            mode='honor'
        )
        cls.certificate = GeneratedCertificateFactory.create(
            user=cls.user,
            course_id=cls.course.id,
            mode='honor',
            download_url=cls.download_url,
            status='downloadable',
            grade=0.98
        )
        cls.course.certificates = {'certificates': [{'course_title': cls.course.display_name}]}
        with cls.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, cls.course.id):
            cls.store.update_item(cls.course, cls.user.username)

    def setUp(self):
        super(GenerateStudentCertificateViewsTestCase, self).setUp()

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    @mock.patch('openedx.features.student_certificates.views.render_to_response')
    def test_student_certificates(self, mock_method):
        """
            Tests the flow of certificate generation.
        """
        expected_context = {
            'user_certificates': [
                {
                    'social_sharing_urls': get_philu_certificate_social_context(self.course, self.certificate),
                    'course_name': self.course.display_name,
                    'course_title': self.course.display_name,
                    'certificate_url': '%s%s' % (settings.LMS_ROOT_URL, self.download_url),
                    'course_start': self.course.start.strftime('%b %d, %Y') if self.course.start else None,
                    'completion_date': self.course.end.strftime('%b %d, %Y') if self.course.end else None
                }
            ]
        }

        request = HttpRequest()
        request.user = self.user
        student_certificates(request)
        mock_method.assert_called_once_with('certificates.html', expected_context)

    @mock.patch('openedx.features.student_certificates.views.render_to_response')
    def test_student_certificates_course_title_type_error(self, mock_method):
        """
            Test certificate generation flow if certificate shows type error.
        """
        self.course.certificates = {'certificates': {}}
        self.course.save()
        self.store.update_item(self.course, self.user.id)

        expected_context = {
            'user_certificates': [
                {
                    'social_sharing_urls': get_philu_certificate_social_context(self.course, self.certificate),
                    'course_name': self.course.display_name,
                    'course_title': self.course.display_name,
                    'certificate_url': '%s%s' % (settings.LMS_ROOT_URL, self.download_url),
                    'course_start': self.course.start.strftime('%b %d, %Y') if self.course.start else None,
                    'completion_date': self.course.end.strftime('%b %d, %Y') if self.course.end else None
                }
            ]
        }

        request = HttpRequest()
        request.user = self.user
        student_certificates(request)
        mock_method.assert_called_once_with('certificates.html', expected_context)
    
    @mock.patch('openedx.features.student_certificates.views.render_to_response')
    def test_student_certificates_course_title_index_error(self, mock_method):
        """
            Test certificate generation flow if certificate object is not as it was expected.
        """
        self.course.certificates = {'certificates': []}
        self.course.save()
        self.store.update_item(self.course, self.user.id)

        expected_context = {
            'user_certificates': [
                {
                    'social_sharing_urls': get_philu_certificate_social_context(self.course, self.certificate),
                    'course_name': self.course.display_name,
                    'course_title': self.course.display_name,
                    'certificate_url': '%s%s' % (settings.LMS_ROOT_URL, self.download_url),
                    'course_start': self.course.start.strftime('%b %d, %Y') if self.course.start else None,
                    'completion_date': self.course.end.strftime('%b %d, %Y') if self.course.end else None
                }
            ]
        }

        request = HttpRequest()
        request.user = self.user
        student_certificates(request)
        mock_method.assert_called_once_with('certificates.html', expected_context)

    @override_settings(FEATURES=CUSTOM_FEATURES)
    @mock.patch('openedx.features.student_certificates.views.render_to_response')
    def test_student_certificates_html_certificate_enabled(self, mock_method):
        """
            Test certificate generation flow if CERTIFICATES_HTML_VIEW is enabled in settings.FEATURES.
        """

        self.course.cert_html_view_enabled = True
        self.course.certificates = {'certificates': [{'course_title': self.course.display_name, 'is_active': True}]}
        self.store.update_item(self.course, self.user.id)
        expected_context = {
            'user_certificates': [
                {
                    'social_sharing_urls': get_philu_certificate_social_context(self.course, self.certificate),
                    'course_name': self.course.display_name,
                    'course_title': self.course.display_name,
                    'certificate_url': '%s/certificates/%s' % (settings.LMS_ROOT_URL, self.certificate.verify_uuid),
                    'course_start': self.course.start.strftime('%b %d, %Y') if self.course.start else None,
                    'completion_date': self.course.end.strftime('%b %d, %Y') if self.course.end else None
                }
            ]
        }

        request = HttpRequest()
        request.user = self.user
        student_certificates(request)
        mock_method.assert_called_once_with('certificates.html', expected_context)

    @mock.patch('openedx.features.student_certificates.views.render_to_response')
    def test_shared_student_achievements(self, mock_method):
        """
            Test certificate sharing web-view flow.
        """
        request = HttpRequest()
        request.user = self.user
        shared_student_achievements(request, self.certificate.verify_uuid)
        expected_context = {
            'meta_tags': {
                'description': '',
                'title': TWITTER_META_TITLE_FMT.format(course_name=self.course.display_name),
                'image': 'https://s3.amazonaws.com/edxuploads/certificates_images/{0}.jpg'.format(self.certificate.verify_uuid), 
                'robots': '', 
                'utm_params': {}, 
                'keywords': ''
                }, 
            'course_url': COURSE_URL_FMT.format(
                base_url = settings.LMS_ROOT_URL,
                course_url = 'courses',
                course_id = self.course.id,
                about_url = 'about'
            )
        }
        mock_method.assert_called_once_with('shared_certificate.html', expected_context)

    def test_shared_student_achievements_certificate_not_found(self):
        """
            Test to check if the shared student certificate gives error on deleted/non-existing certificates or not.
        """
        verify_uuid = self.certificate.verify_uuid
        self.certificate.delete()
        request = HttpRequest()
        request.user = self.user

        with self.assertRaises(Http404):
            shared_student_achievements(request, verify_uuid)
