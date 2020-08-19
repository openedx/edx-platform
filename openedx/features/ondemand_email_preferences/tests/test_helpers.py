"""
Tests for ondemand email preferences helpers
"""
from datetime import datetime

import mock
from django.conf import settings
from django.core.urlresolvers import reverse

from openedx.features.ondemand_email_preferences.helpers import (
    ON_DEMAND_MODULE_TEXT,
    get_chapters_text,
    get_my_account_link
)
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

USER_ACCOUNT_FORMATTER = '{base_url}{my_account_url}?course_id={course_id}'


class OnDemandEmailPreferencesHelpers(ModuleStoreTestCase):
    """
    This class contains all tests for ondemand preferences helpers.
    """

    def setUp(self):
        super(OnDemandEmailPreferencesHelpers, self).setUp()
        self.course = CourseFactory.create(display_name='test course', run='Testing_course')

    @mock.patch('openedx.features.ondemand_email_preferences.helpers.get_next_date')
    @mock.patch('openedx.features.ondemand_email_preferences.helpers.get_course_open_date')
    @mock.patch('openedx.features.ondemand_email_preferences.helpers.get_current_request')
    @mock.patch('openedx.features.ondemand_email_preferences.helpers.toc_for_course')
    def test_get_chapters_text(self, mock_toc_for_course, mock_get_current_request,
                               mock_get_course_open_date, mock_get_next_date):
        """
        Test 'get_chapters_text', html string that contains chapter name with completion date wrapped in <li> tags.
        """
        user = UserFactory()
        CourseEnrollmentFactory.create(user=user, course_id=self.course.id, mode='honor')

        first_module_name = 'Chapter 1'
        second_module_name = 'Chapter 2'
        first_module_completion_date = '2020-02-09'
        second_module_completion_date = '2020-02-16'

        mock_toc_for_course.return_value = {
            'chapters': [
                {
                    'display_name': first_module_name,
                },
                {
                    'display_name': second_module_name,
                }
            ]
        }

        mock_get_current_request.return_value = mock.ANY
        mock_get_course_open_date.return_value = datetime.strptime('2020-02-02', '%Y-%m-%d')
        mock_get_next_date.side_effect = [first_module_completion_date, second_module_completion_date]

        expected_output = '{module_1}{module_2}'.format(
            module_1=ON_DEMAND_MODULE_TEXT.format(module_name=first_module_name,
                                                  module_comp_date=first_module_completion_date),
            module_2=ON_DEMAND_MODULE_TEXT.format(module_name=second_module_name,
                                                  module_comp_date=second_module_completion_date)
        )

        actual_output = get_chapters_text(self.course.id, user)
        self.assertEqual(expected_output, actual_output)

    def test_get_my_account_link(self):
        """
        Test user's account link.
        """
        my_account_url = reverse('update_account_settings')
        expected_output = USER_ACCOUNT_FORMATTER.format(
            base_url=settings.LMS_ROOT_URL, my_account_url=my_account_url, course_id=str(self.course.id)
        )
        actual_output = get_my_account_link(self.course.id)
        self.assertEqual(expected_output, actual_output)
