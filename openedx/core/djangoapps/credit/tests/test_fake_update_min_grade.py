"""
Tests for the fake page for updating min grade status.
"""

from django.conf import settings
from django.test import TestCase

from mock import patch
from unittest import skipUnless

from student.tests.factories import UserFactory
from util.testing import UrlResetMixin


@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')
class UpdateMinGradeRequirementFakeViewTest(UrlResetMixin, TestCase):
    """
    Base class to test the fake view.
    """
    def setUp(self, **kwargs):
        enable_credit_eligibility = kwargs.get('enable_credit_eligibility', False)
        with patch.dict('django.conf.settings.FEATURES', {
            'ENABLE_CREDIT_ELIGIBILITY': True,
            'ENABLE_MIN_GRADE_STATUS_UPDATE': enable_credit_eligibility
        }):
            super(UpdateMinGradeRequirementFakeViewTest, self).setUp('openedx.core.djangoapps.credit.urls')

        self.user = UserFactory.create(username="test", password="test")
        self.client.login(username="test", password="test")


class UpdateMinGradeRequirementFakeViewDisabledTest(UpdateMinGradeRequirementFakeViewTest):
    """Test the fake software secure response when feature flag
    'ENABLE_MIN_GRADE_STATUS_UPDATE' is not enabled.
    """
    def setUp(self):
        super(UpdateMinGradeRequirementFakeViewDisabledTest, self).setUp(enable_credit_eligibility=False)

    def test_get_method_without_enable_feature_flag(self):
        """
        Test that the user gets 404 response if the feature flag
        'ENABLE_MIN_GRADE_STATUS_UPDATE' is not enabled.
        """
        response = self.client.get(
            'credit/check_grade/'
        )

        self.assertEqual(response.status_code, 404)


class UpdateMinGradeRequirementFakeViewEnabledTest(UpdateMinGradeRequirementFakeViewTest):
    """Test the fake page when feature flag 'ENABLE_MIN_GRADE_STATUS_UPDATE'
    is enabled.
    """
    def setUp(self):
        super(UpdateMinGradeRequirementFakeViewEnabledTest, self).setUp(enable_credit_eligibility=True)

    def test_get_method_without_logged_in_user(self):
        """
        Test that the user gets 302 response if that user is not logged in.
        """
        self.client.logout()
        response = self.client.get(
            '/credit/check_grade'
        )
        self.assertEqual(response.status_code, 302)

    def test_get_method(self):
        """
        Test that GET method of fake view.
        """
        response = self.client.get(
            '/credit/check_grade/'
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Fake Credit Eligibility', response.content)
