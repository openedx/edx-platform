# -*- coding: utf-8 -*-
""" Tests for student profile views. """

import datetime
import ddt

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from util.testing import UrlResetMixin

from course_modes.models import CourseMode

from certificates.tests.factories import GeneratedCertificateFactory  # pylint: disable=import-error
from student.tests.factories import CourseEnrollmentFactory, UserFactory

from openedx.features.learner_profile.views.learner_profile import learner_profile_context
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class LearnerProfileViewTest(UrlResetMixin, ModuleStoreTestCase):
    """ Tests for the student profile view. """

    USERNAME = "username"
    OTHER_USERNAME = "other_user"
    PASSWORD = "password"
    DOWNLOAD_URL = "http://www.example.com/certificate.pdf"
    CONTEXT_DATA = [
        'default_public_account_fields',
        'accounts_api_url',
        'preferences_api_url',
        'account_settings_page_url',
        'has_preferences_access',
        'own_profile',
        'country_options',
        'language_options',
        'account_settings_data',
        'preferences_data',
    ]

    def setUp(self):
        super(LearnerProfileViewTest, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        self.other_user = UserFactory.create(username=self.OTHER_USERNAME, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.course = CourseFactory.create(
            start=datetime.datetime(2013, 9, 16, 7, 17, 28),
            end=datetime.datetime.now(),
            certificate_available_date=datetime.datetime.now(),
        )

    def test_context(self):
        """
        Verify learner profile page context data.
        """
        request = RequestFactory().get('/url')
        request.user = self.user

        context = learner_profile_context(request, self.USERNAME, self.user.is_staff)

        self.assertEqual(
            context['data']['default_public_account_fields'],
            settings.ACCOUNT_VISIBILITY_CONFIGURATION['public_fields']
        )

        self.assertEqual(
            context['data']['accounts_api_url'],
            reverse("accounts_api", kwargs={'username': self.user.username})
        )

        self.assertEqual(
            context['data']['preferences_api_url'],
            reverse('preferences_api', kwargs={'username': self.user.username})
        )

        self.assertEqual(
            context['data']['profile_image_upload_url'],
            reverse("profile_image_upload", kwargs={'username': self.user.username})
        )

        self.assertEqual(
            context['data']['profile_image_remove_url'],
            reverse('profile_image_remove', kwargs={'username': self.user.username})
        )

        self.assertEqual(
            context['data']['profile_image_max_bytes'],
            settings.PROFILE_IMAGE_MAX_BYTES
        )

        self.assertEqual(
            context['data']['profile_image_min_bytes'],
            settings.PROFILE_IMAGE_MIN_BYTES
        )

        self.assertEqual(context['data']['account_settings_page_url'], reverse('account_settings'))

        for attribute in self.CONTEXT_DATA:
            self.assertIn(attribute, context['data'])

    def test_view(self):
        """
        Verify learner profile page view.
        """
        profile_path = reverse('learner_profile', kwargs={'username': self.USERNAME})
        response = self.client.get(path=profile_path)

        for attribute in self.CONTEXT_DATA:
            self.assertIn(attribute, response.content)

    def test_undefined_profile_page(self):
        """
        Verify that a 404 is returned for a non-existent profile page.
        """
        profile_path = reverse('learner_profile', kwargs={'username': "no_such_user"})
        response = self.client.get(path=profile_path)
        self.assertEqual(404, response.status_code)

    def _create_certificate(self, enrollment_mode):
        """Simulate that the user has a generated certificate. """
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, mode=enrollment_mode)
        return GeneratedCertificateFactory(
            user=self.user,
            course_id=self.course.id,
            mode=enrollment_mode,
            download_url=self.DOWNLOAD_URL,
            status="downloadable"
        )

    @ddt.data(CourseMode.HONOR, CourseMode.PROFESSIONAL, CourseMode.VERIFIED)
    def test_certificate_visibility(self, cert_mode):
        """
        Verify that certificates are displayed with the correct card mode.
        """
        # Add new certificate
        cert = self._create_certificate(cert_mode)
        cert.save()

        request = RequestFactory().get('/url')
        request.user = self.user
        context = learner_profile_context(request, self.user.username, self.user.is_staff)

        self.assertTrue('card certificate-card mode-' + cert_mode in str(context['achievements_fragment'].content))

    @ddt.data(True, False)
    def test_no_certificate_visibility(self, own_profile):
        """
        Verify that the 'You haven't earned any certificates yet.' well appears on the user's
        own profile when they do not have certificates and does not appear when viewing
        another user that does not have any certificates.
        """
        request = RequestFactory().get('/url')
        request.user = self.user
        profile_username = self.user.username if own_profile else self.other_user.username
        context = learner_profile_context(request, profile_username, self.user.is_staff)

        if own_profile:
            content = str(context['achievements_fragment'].content)
            self.assertIn('icon fa fa-search', content)
            self.assertIn("You haven't earned any certificates yet", content)
        else:
            self.assertIsNone(context['achievements_fragment'])
