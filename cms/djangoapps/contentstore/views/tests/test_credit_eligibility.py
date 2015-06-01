"""
Unit tests for credit eligibility methods.
"""
from mock import patch

from contentstore.tests.utils import CourseTestCase
from student.tests.factories import UserFactory
from util.testing import UrlResetMixin
from xmodule.modulestore.tests.factories import CourseFactory


class CreditEligibilityViewTest(UrlResetMixin, CourseTestCase):
    """
    Base class to test the credit eligibility view.
    """
    def setUp(self, **kwargs):
        enable_credit_eligibility = kwargs.get('enable_credit_eligibility', False)
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_CREDIT_ELIGIBILITY': enable_credit_eligibility}):
            super(CreditEligibilityViewTest, self).setUp('cms.urls')

        self.user = UserFactory(is_staff=True)  # pylint: disable=no-member
        self.client.login(username=self.user.username, password='test')
        self.course = CourseFactory.create(org='edX', number='dummy', display_name='Credit Course')
        self.credit_eligibility_url = (
            '/view_credit_eligibility'
            '/{course_key}'
        ).format(course_key=unicode(self.course.id))


class CreditEligibilityViewDisabledTest(CreditEligibilityViewTest):
    """
    Test the credit eligibility view response when feature flag
    'ENABLE_CREDIT_ELIGIBILITY' is not enabled.
    """
    def setUp(self):
        super(CreditEligibilityViewDisabledTest, self).setUp(enable_credit_eligibility=False)

    def test_get_method_without_enable_feature_flag(self):
        """
        Test that the user gets 404 response if the feature flag
        'ENABLE_CREDIT_ELIGIBILITY' is not enabled.
        """
        response = self.client.get(self.credit_eligibility_url)
        self.assertEqual(response.status_code, 404)


class CreditEligibilityViewEnabledTest(CreditEligibilityViewTest):
    """
    Test the credit eligibility view response when feature flag
    'ENABLE_CREDIT_ELIGIBILITY' is enabled.
    """
    def setUp(self):
        super(CreditEligibilityViewEnabledTest, self).setUp(enable_credit_eligibility=True)

    def test_get_method_without_logged_in_user(self):
        """
        Test that the user gets 302 response if that user is not logged in.
        """
        self.client.logout()
        response = self.client.get(self.credit_eligibility_url)
        self.assertEqual(response.status_code, 302)

    def test_get_method(self):
        """
        Test that GET method of credit eligibility view gives 200 response
        for the logged-in user.
        """
        response = self.client.get(self.credit_eligibility_url)
        self.assertEqual(response.status_code, 200)
