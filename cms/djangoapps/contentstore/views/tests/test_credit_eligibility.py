"""
Unit tests for credit eligibility UI in Studio.
"""

import mock

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url
from xmodule.modulestore.tests.factories import CourseFactory

from openedx.core.djangoapps.credit.api import get_credit_requirements
from openedx.core.djangoapps.credit.models import CreditCourse
from openedx.core.djangoapps.credit.signals import on_course_publish


class CreditEligibilityTest(CourseTestCase):
    """Base class to test the course settings details view in Studio for credit
    eligibility requirements.
    """
    def setUp(self):
        super(CreditEligibilityTest, self).setUp()
        self.course = CourseFactory.create(org='edX', number='dummy', display_name='Credit Course')
        self.course_details_url = reverse_course_url('settings_handler', unicode(self.course.id))

    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_CREDIT_ELIGIBILITY': False})
    def test_course_details_with_disabled_setting(self):
        """Test that user don't see credit eligibility requirements in response
        if the feature flag 'ENABLE_CREDIT_ELIGIBILITY' is not enabled.
        """
        response = self.client.get_html(self.course_details_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Course Credit Requirements")
        self.assertNotContains(response, "Steps required to earn course credit")

    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_CREDIT_ELIGIBILITY': True})
    def test_course_details_with_enabled_setting(self):
        """Test that credit eligibility requirements are present in
        response if the feature flag 'ENABLE_CREDIT_ELIGIBILITY' is enabled.
        """
        # verify that credit eligibility requirements block don't show if the
        # course is not set as credit course
        response = self.client.get_html(self.course_details_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Course Credit Requirements")
        self.assertNotContains(response, "Steps required to earn course credit")

        # verify that credit eligibility requirements block shows if the
        # course is set as credit course and it has eligibility requirements
        credit_course = CreditCourse(course_key=unicode(self.course.id), enabled=True)
        credit_course.save()
        self.assertEqual(len(get_credit_requirements(self.course.id)), 0)
        # test that after publishing course, minimum grade requirement is added
        on_course_publish(self.course.id)
        self.assertEqual(len(get_credit_requirements(self.course.id)), 1)

        response = self.client.get_html(self.course_details_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Course Credit Requirements")
        self.assertContains(response, "Steps required to earn course credit")
