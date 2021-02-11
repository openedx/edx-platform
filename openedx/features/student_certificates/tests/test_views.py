"""
This file contains the test cases for views of the student_certificates application.
"""

import factory  # pylint: disable=unused-import
import mock
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import signals
from django.http import Http404, HttpRequest
from django.test import RequestFactory
from django.test.utils import override_settings

from certificates.tests.factories import GeneratedCertificateFactory
from custom_settings.models import CustomSettings
from lms.djangoapps.onboarding.helpers import get_current_utc_date
from openedx.core.djangolib.testing.philu_utils import configure_philu_theme
from openedx.features.student_certificates.constants import COURSE_URL_FMT, TWITTER_META_TITLE_FMT
from openedx.features.student_certificates.helpers import get_philu_certificate_social_context
from openedx.features.student_certificates.views import (
    download_certificate_pdf,
    shared_student_achievements,
    student_certificates
)
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


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
        configure_philu_theme()

        cls.download_url = '/certificate.pdf'
        cls.course = CourseFactory.create()
        cls.course.certificates_display_behavior = 'early_with_info'
        cls.username = 'test_user'
        cls.password = 'password'

        from openedx.features.course_card.tests.helpers import initialize_test_user
        cls.user = initialize_test_user(password=cls.password)
        cls.user.save()
        cls.course_settings = CustomSettings(
            id=cls.course.id, course_short_id=1, course_open_date=get_current_utc_date()
        )
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

        cls.factory = RequestFactory()

    # pylint: disable=no-member
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
                'image': 'https://s3.amazonaws.com/edxuploads/certificates_images/{0}.jpg'.format(
                    self.certificate.verify_uuid
                ),
                'robots': '',
                'utm_params': {},
                'keywords': ''
            },
            'course_url': COURSE_URL_FMT.format(
                base_url=settings.LMS_ROOT_URL,
                course_url='courses',
                course_id=self.course.id,
                about_url='about'
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

    # pylint: disable=no-member
    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    @mock.patch('openedx.features.student_certificates.views.get_pdf_data_by_certificate_uuid')
    def test_download_certificate_pdf(self, mock_get_pdf_data_by_certificate_uuid):
        """
        Tests the flow of certificate pdf downloading
        """
        certificate_uuid = self.certificate.verify_uuid

        mock_get_pdf_data_by_certificate_uuid.return_value = 'PDF Bytes data'

        request = self.factory.get(reverse('download_certificate_pdf', args=(certificate_uuid,)))
        request.user = self.user
        response = download_certificate_pdf(request, certificate_uuid)

        mock_get_pdf_data_by_certificate_uuid.assert_called_once_with(certificate_uuid)

        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="PhilanthropyUniversity_Run0.pdf"')
