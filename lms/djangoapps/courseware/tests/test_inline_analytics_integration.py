"""Inline Analytics integration tests"""

import json
from mock import patch

from django.test import RequestFactory
from django.test.utils import override_settings

from courseware.views import get_analytics_answer_dist, process_analytics_answer_dist
from courseware.tests.factories import UserFactory, InstructorFactory, StaffFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from analyticsclient.exceptions import NotFoundError, InvalidRequestError, TimeoutError

ZENDESK_URL = 'https://zendesk.com'


class InlineAnalyticsAnswerDistribution(ModuleStoreTestCase):

    def setUp(self):
        super(InlineAnalyticsAnswerDistribution, self).setUp()
        self.user = UserFactory.create()
        self.factory = RequestFactory()
        self.course = CourseFactory.create(
            org='A',
            number='B',
            display_name='C',
        )
        self.instructor = InstructorFactory(course_key=self.course.id)

        analytics_data = {
            'module_id': '123',
            'question_types_by_part': 'radio',
            'num_options_by_part': 6,
            'course_id': 'A/B/C',
        }
        json_analytics_data = json.dumps(analytics_data)
        self.data = json_analytics_data
        self.zendesk_response = (
            'A problem has occurred retrieving the data, to report the problem click '
            '<a href="{ZENDESK_URL}/hc/en-us/requests/new">here</a>'
        ).format(ZENDESK_URL=ZENDESK_URL)

    @override_settings(ZENDESK_URL=ZENDESK_URL)
    def test_no_url(self):
        request = self.factory.post('', self.data, content_type='application/json')
        request.user = self.instructor

        response = get_analytics_answer_dist(request)
        self.assertEquals(response.content, self.zendesk_response)

    @override_settings(ZENDESK_URL=None)
    def test_no_url_no_zendesk(self):
        request = self.factory.post('', self.data, content_type='application/json')
        request.user = self.instructor

        response = get_analytics_answer_dist(request)
        self.assertEquals(response.content, 'A problem has occurred retrieving the data.')

    def test_process_analytics_answer_dist(self):
        """
        Test with data that is complete.
        """
        data = [
            {
                'course_id': 'A/B/C',
                'module_id': 'i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2',
                'part_id': 'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1',
                'correct': False,
                'first_response_count': 7,
                'last_response_count': 8,
                'value_id': 'choice_0',
                'answer_value_text': 'Option 1',
                'answer_value_numeric': 'null',
                'variant': None,
                'created': '2014-10-15T101351',
            },
            {
                'course_id': 'A/B/C',
                'module_id': 'i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2',
                'part_id': 'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1',
                'correct': True,
                'first_response_count': 23,
                'last_response_count': 24,
                'value_id': 'choice_1',
                'answer_value_text': 'Option 2',
                'answer_value_numeric': 'null',
                'variant': None,
                'created': '2014-10-15T101351',
            },
        ]

        question_types_by_part = {
            'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': 'radio',
        }

        num_options_by_part = {
            'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': 4,
        }

        processed_data = {
            'count_by_part': {
                'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': {
                    'totalFirstIncorrectCount': 7,
                    'totalLastIncorrectCount': 8,
                    'totalFirstAttemptCount': 30,
                    'totalLastAttemptCount': 32,
                    'totalFirstCorrectCount': 23,
                    'totalLastCorrectCount': 24,
                },
            },
            'data_by_part': {
                'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': [
                    {
                        'first_count': 7,
                        'last_count': 8,
                        'value_id': 'choice_0',
                        'correct': False,
                    },
                    {
                        'first_count': 23,
                        'last_count': 24,
                        'value_id': 'choice_1',
                        'correct': True,
                    },
                ]
            },
            'message_by_part': {
            },
            'last_update_date': 'Oct 15, 2014 at 10:13 UTC'
        }

        return_json = process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)
        self.assertEquals(json.loads(return_json.content), processed_data)

    def test_process_analytics_answer_dist_missing_correct(self):
        """
        Test with data that has correct answer missing.
        """
        data = [
            {
                'course_id': 'A/B/C',
                'module_id': 'i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2',
                'part_id': 'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1',
                'correct': False,
                'first_response_count': 7,
                'last_response_count': 9,
                'value_id': 'choice_0',
                'answer_value_text': 'Option 1',
                'answer_value_numeric': 'null',
                'variant': None,
                'created': '2014-10-15T101351',
            },
        ]

        question_types_by_part = {
            'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': 'radio',
        }

        num_options_by_part = {
            'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': 4,
        }

        processed_data = {
            'count_by_part': {
                'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': {
                    'totalFirstIncorrectCount': 7,
                    'totalLastIncorrectCount': 9,
                    'totalFirstAttemptCount': 7,
                    'totalLastAttemptCount': 9,
                    'totalFirstCorrectCount': 0,
                    'totalLastCorrectCount': 0,
                },
            },
            'data_by_part': {
                'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': [
                    {
                        'first_count': 7,
                        'last_count': 9,
                        'value_id': 'choice_0',
                        'correct': False,
                    },
                ]
            },
            'message_by_part': {
            },
            'last_update_date': 'Oct 15, 2014 at 10:13 UTC'
        }

        return_json = process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)
        self.assertEquals(json.loads(return_json.content), processed_data)

    def test_process_analytics_answer_dist_variant(self):
        """
        Test with data that has variant (radomization) set.
        """
        data = [
            {
                'course_id': 'A/B/C',
                'module_id': 'i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2',
                'part_id': 'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1',
                'correct': False,
                'first_response_count': 7,
                'last_response_count': 7,
                'value_id': 'choice_0',
                'answer_value_text': 'Option 1',
                'answer_value_numeric': 'null',
                'variant': '123',
                'created': '2014-10-15T101351',
            },
            {
                'course_id': 'A/B/C',
                'module_id': 'i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2',
                'part_id': 'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1',
                'correct': True,
                'first_response_count': 23,
                'last_response_count': 23,
                'value_id': 'choice_1',
                'answer_value_text': 'Option 2',
                'answer_value_numeric': 'null',
                'variant': None,
                'created': '2014-10-15T101351',
            },
        ]

        question_types_by_part = {
            'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': 'radio',
        }

        num_options_by_part = {
            'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': 4,
        }

        processed_data = {
            'count_by_part': {
                'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': {
                    'totalFirstIncorrectCount': 0,
                    'totalLastIncorrectCount': 0,
                    'totalFirstAttemptCount': 23,
                    'totalLastAttemptCount': 23,
                    'totalFirstCorrectCount': 23,
                    'totalLastCorrectCount': 23,
                },
            },
            'data_by_part': {
                'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': [
                    {
                        'first_count': 23,
                        'last_count': 23,
                        'value_id': 'choice_1',
                        'correct': True,
                    },
                ]
            },
            'message_by_part': {
                'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': (
                    'The analytics cannot be displayed for this question as randomization was set at '
                    'one time.'
                )
            },
            'last_update_date': 'Oct 15, 2014 at 10:13 UTC'
        }

        return_json = process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)
        self.assertEquals(json.loads(return_json.content), processed_data)

    def test_process_analytics_answer_dist_radio(self):
        """
        Test with data having more rows than choices for radio type.
        """
        data = [
            {
                'course_id': 'A/B/C',
                'module_id': 'i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2',
                'part_id': 'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1',
                'correct': False,
                'count': 7,
                'value_id': 'choice_0',
                'answer_value_text': 'Option 1',
                'answer_value_numeric': 'null',
                'variant': '123',
                'created': '2014-10-15T101351',
            },
            {
                'course_id': 'A/B/C',
                'module_id': 'i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2',
                'part_id': 'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1',
                'correct': True,
                'count': 23,
                'value_id': 'choice_1',
                'answer_value_text': 'Option 2',
                'answer_value_numeric': 'null',
                'variant': None,
                'created': '2014-10-15T101351',
            },
        ]

        question_types_by_part = {
            "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": "radio",
        }

        num_options_by_part = {
            'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': 1,
        }

        processed_data = {
            'count_by_part': {
            },
            'data_by_part': {
            },
            'message_by_part': {
                'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': (
                    'The analytics cannot be displayed for this question as the number of rows returned did '
                    'not match the question definition.'
                )
            },
            'last_update_date': 'Oct 15, 2014 at 10:13 UTC'
        }

        return_json = process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)
        self.assertEquals(json.loads(return_json.content), processed_data)

    def test_process_analytics_answer_dist_checkbox(self):
        """
        Test with data having more rows than is possible for checkbox type.
        """
        data = [
            {
                'course_id': 'A/B/C',
                'module_id': 'i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2',
                'part_id': 'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1',
                'correct': False,
                'count': 7,
                'value_id': 'choice_0',
                'answer_value_text': 'Option 1',
                'answer_value_numeric': 'null',
                'variant': '123',
                'created': '2014-10-15T101351',
            },
            {
                'course_id': 'A/B/C',
                'module_id': 'i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2',
                'part_id': 'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1',
                'correct': True,
                'count': 23,
                'value_id': 'choice_1',
                'answer_value_text': 'Option 2',
                'answer_value_numeric': 'null',
                'variant': None,
                'created': '2014-10-15T101351',
            },
        ]

        question_types_by_part = {
            'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': 'checkbox',
        }

        num_options_by_part = {
            'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': 0,
        }

        processed_data = {
            'count_by_part': {
            },
            'data_by_part': {
            },
            'message_by_part': {
                'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': (
                    'The analytics cannot be displayed for this question as the number of rows returned did '
                    'not match the question definition.'
                )
            },
            'last_update_date': 'Oct 15, 2014 at 10:13 UTC'
        }

        return_json = process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)
        self.assertEquals(json.loads(return_json.content), processed_data)

    def test_process_analytics_answer_dist_inconsistency(self):
        """
        Test with data having part_id that doesn't exist in the problem definition.
        """
        data = [
            {
                'course_id': 'A/B/C',
                'module_id': 'i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2',
                'part_id': 'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1',
                'correct': False,
                'count': 7,
                'value_id': 'null',
                'answer_value_text': 8,
                'answer_value_numeric': 'null',
                'variant': None,
                'created': '2014-10-15T101351',
            },
        ]

        question_types_by_part = {
            'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_2': 'option',
        }

        num_options_by_part = {
            'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_2': 0,
        }

        processed_data = {
            'count_by_part': {
            },
            'data_by_part': {
            },
            'message_by_part': {
                'i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1': (
                    'The analytics cannot be displayed as there is an inconsistency in the data.'
                )
            },
            'last_update_date': 'Oct 15, 2014 at 10:13 UTC'
        }

        return_json = process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)
        self.assertEquals(json.loads(return_json.content), processed_data)


@override_settings(ANALYTICS_DATA_URL='dummy_url',
                   ZENDESK_URL=ZENDESK_URL)
class InlineAnalyticsAnswerDistributionWithOverrides(ModuleStoreTestCase):

    def setUp(self):
        super(InlineAnalyticsAnswerDistributionWithOverrides, self).setUp()
        self.user = UserFactory.create()
        self.factory = RequestFactory()
        self.course = CourseFactory.create(
            org='A',
            number='B',
            display_name='C',
        )
        self.staff = StaffFactory(course_key=self.course.id)
        self.instructor = InstructorFactory(course_key=self.course.id)

        analytics_data = {
            'module_id': '123',
            'question_types_by_part': 'radio',
            'num_options_by_part': 6,
            'course_id': 'A/B/C',
        }
        json_analytics_data = json.dumps(analytics_data)
        self.data = json_analytics_data
        self.zendesk_response = (
            'A problem has occurred retrieving the data, to report the problem click '
            '<a href="{ZENDESK_URL}/hc/en-us/requests/new">here</a>'
        ).format(ZENDESK_URL=ZENDESK_URL)

    def test_regular_user(self):
        request = self.factory.post('', self.data, content_type='application/json')
        request.user = self.user

        response = get_analytics_answer_dist(request)
        self.assertEquals(response.content, self.zendesk_response)

    @patch('courseware.views.process_analytics_answer_dist')
    @patch('courseware.views.Client')
    def test_staff_and_url(self, mock_client, mock_process_analytics):
        mock_client.return_value.modules.return_value.answer_distribution.return_value = [{}]
        factory = self.factory
        request = factory.post('', self.data, content_type='application/json')
        request.user = self.staff

        mock_process_analytics.return_value = [{'dummy': 'dummy'}]
        response = get_analytics_answer_dist(request)
        self.assertEquals(response, [{'dummy': 'dummy'}])

    @patch('courseware.views.process_analytics_answer_dist')
    @patch('courseware.views.Client')
    def test_instructor_and_url(self, mock_client, mock_process_analytics):
        mock_client.return_value.modules.return_value.answer_distribution.return_value = [{}]

        factory = self.factory
        request = factory.post('', self.data, content_type='application/json')
        request.user = self.instructor

        mock_process_analytics.return_value = [{'dummy': 'dummy'}]
        response = get_analytics_answer_dist(request)
        self.assertEquals(response, [{'dummy': 'dummy'}])

    @patch('courseware.views.Client')
    def test_not_found_error(self, mock_client):
        mock_client.return_value.modules.return_value.answer_distribution.side_effect = NotFoundError

        factory = self.factory
        request = factory.post('', self.data, content_type='application/json')
        request.user = self.instructor

        response = get_analytics_answer_dist(request)
        self.assertEquals(response.status_code, 404)
        self.assertEquals(response.content, 'There are no student answers for this problem yet; please try again later.')

    @patch('courseware.views.Client')
    def test_invalid_request_error(self, mock_client):
        mock_client.return_value.modules.return_value.answer_distribution.side_effect = InvalidRequestError

        factory = self.factory
        request = factory.post('', self.data, content_type='application/json')
        request.user = self.instructor

        response = get_analytics_answer_dist(request)
        self.assertEquals(response.status_code, 500)
        self.assertEquals(response.content, self.zendesk_response)

    @patch('courseware.views.Client')
    def test_timeout_error(self, mock_client):
        mock_client.return_value.modules.return_value.answer_distribution.side_effect = TimeoutError

        factory = self.factory
        request = factory.post('', self.data, content_type='application/json')
        request.user = self.instructor

        response = get_analytics_answer_dist(request)
        self.assertEquals(response.status_code, 500)
        self.assertEquals(response.content, self.zendesk_response)
