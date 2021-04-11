"""
Tests for the fake software secure response.
"""


from django.test import TestCase
from mock import patch

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.util.testing import UrlResetMixin


class SoftwareSecureFakeViewTest(UrlResetMixin, TestCase):
    """
    Base class to test the fake software secure view.
    """

    URLCONF_MODULES = ['lms.djangoapps.verify_student.urls']

    def setUp(self, **kwargs):
        enable_software_secure_fake = kwargs.get('enable_software_secure_fake', False)
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_SOFTWARE_SECURE_FAKE': enable_software_secure_fake}):
            super(SoftwareSecureFakeViewTest, self).setUp()

        self.user = UserFactory.create(username="test", password="test")
        self.attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        self.client.login(username="test", password="test")


class SoftwareSecureFakeViewDisabledTest(SoftwareSecureFakeViewTest):
    """
    Test the fake software secure response when feature flag
    'ENABLE_SOFTWARE_SECURE_FAKE' is not enabled.
    """

    def setUp(self):
        super(SoftwareSecureFakeViewDisabledTest, self).setUp(enable_software_secure_fake=False)

    def test_get_method_without_enable_feature_flag(self):
        """
        Test that the user gets 404 response if the feature flag
        'ENABLE_SOFTWARE_SECURE_FAKE' is not enabled.
        """
        response = self.client.get(
            '/verify_student/software-secure-fake-response'
        )

        self.assertEqual(response.status_code, 404)


class SoftwareSecureFakeViewEnabledTest(SoftwareSecureFakeViewTest):
    """
    Test the fake software secure response when feature flag
    'ENABLE_SOFTWARE_SECURE_FAKE' is enabled.
    """

    def setUp(self):
        super(SoftwareSecureFakeViewEnabledTest, self).setUp(enable_software_secure_fake=True)

    def test_get_method_without_logged_in_user(self):
        """
        Test that the user gets 302 response if that user is not logged in.
        """
        self.client.logout()
        response = self.client.get(
            '/verify_student/software-secure-fake-response'
        )
        self.assertEqual(response.status_code, 302)

    def test_get_method(self):
        """
        Test that GET method of fake software secure view uses the most recent
        attempt for the logged-in user.
        """
        response = self.client.get(
            '/verify_student/software-secure-fake-response'
        )

        self.assertContains(response, 'EdX-ID')
        self.assertContains(response, 'results_callback')
