"""Inline Analytics integration tests"""

import unittest
import json
from mock import patch

from rest_framework.test import APIRequestFactory
from django.test.utils import override_settings

from courseware.views import get_analytics_answer_dist, process_analytics_answer_dist
from courseware.tests.factories import UserFactory
from student.tests.factories import AdminFactory


class InlineAnalyticsTest(unittest.TestCase):
    """ unittest class """

    def setUp(self):
        self.user = UserFactory.create()
        self.instructor = AdminFactory.create()
        self.factory = APIRequestFactory()

    def test_post_request(self):

        request = self.factory.post('')
        response = get_analytics_answer_dist(request)
        self.assertEquals(405, response.status_code)

    @override_settings(ANALYTICS_ANSWER_DIST_URL='dummy_url')
    def test_regular_user(self):

        request = self.factory.get('', {'module_id': '123'})
        request.user = self.user

        response = get_analytics_answer_dist(request)
        self.assertEquals(response.content, 'A problem has occurred retrieving the data, please report the problem.')

    def test_no_url(self):

        request = self.factory.get('', {'module_id': '123'})
        request.user = self.instructor

        response = get_analytics_answer_dist(request)
        self.assertEquals(response.content, 'A problem has occurred retrieving the data, please report the problem.')

    @override_settings(ANALYTICS_ANSWER_DIST_URL='dummy_url')
    @patch('urllib2.urlopen')
    @patch('json.loads')
    @patch('courseware.views.process_analytics_answer_dist')
    def test_instructor_and_url(self, mock_process_analytics, mock_json_loads, mock_requests):

        instructor = AdminFactory.create()

        factory = APIRequestFactory()
        request = factory.get('', {'module_id': '123'})
        request.user = instructor

        mock_process_analytics.return_value = [{'dummy': 'dummy'}]

        response = get_analytics_answer_dist(request)
        self.assertEquals(response, [{'dummy': 'dummy'}])

    def test_process_analytics_answer_dist(self):

        data = [
            {
                "course_id": "A/B/C",
                "module_id": "i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2",
                "part_id": "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1",
                "correct": False,
                "count": 7,
                "value_id": "choice_0",
                "answer_value_text": "Option 1",
                "answer_value_numeric": "null",
                "variant": "null",
                "created": "2014-10-15T10:13:51",
            },
            {
                "course_id": "A/B/C",
                "module_id": "i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2",
                "part_id": "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1",
                "correct": True,
                "count": 23,
                "value_id": "choice_1",
                "answer_value_text": "Option 2",
                "answer_value_numeric": "null",
                "variant": "null",
                "created": "2014-10-15T10:13:51",
            },
        ]

        processed_data = {
            "count_by_part": {
                "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": {
                    "totalIncorrectCount": 7,
                    "totalAttemptCount": 30,
                    "totalCorrectCount": 23,
                },
            },
            "data_by_part": {
                "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": [
                    {
                        "count": 7,
                        "value_id": "choice_0",
                        "correct": False,
                    },
                    {
                        "count": 23,
                        "value_id": "choice_1",
                        "correct": True,
                    },
                ]
            },
            "last_update_date": "Oct 15, 2014 at 10:13 UTC"
        }

        return_json = process_analytics_answer_dist(data)
        self.assertEquals(json.loads(return_json.content), processed_data)

    def test_process_analytics_answer_dist_missing_correct(self):

        data = [
            {
                "course_id": "A/B/C",
                "module_id": "i4x://A/B/problem/f3ed0ba7f89445ee9a83541e1fc8a2f2",
                "part_id": "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1",
                "correct": False,
                "count": 7,
                "value_id": "choice_0",
                "answer_value_text": "Option 1",
                "answer_value_numeric": "null",
                "variant": "null",
                "created": "2014-10-15T10:13:51",
            },
        ]

        processed_data = {
            "count_by_part": {
                "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": {
                    "totalIncorrectCount": 7,
                    "totalAttemptCount": 7,
                    "totalCorrectCount": 0,
                },
            },
            "data_by_part": {
                "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": [
                    {
                        "count": 7,
                        "value_id": "choice_0",
                        "correct": False,
                    },
                ]
            },
            "last_update_date": "Oct 15, 2014 at 10:13 UTC"
        }

        return_json = process_analytics_answer_dist(data)
        self.assertEquals(json.loads(return_json.content), processed_data)
