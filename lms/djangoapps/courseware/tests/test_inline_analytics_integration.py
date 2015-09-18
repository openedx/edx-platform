"""Inline Analytics integration tests"""

import json
from mock import patch, MagicMock

from django.test import RequestFactory
from django.test.utils import override_settings

from courseware.views import get_analytics_answer_dist, process_analytics_answer_dist
from courseware.tests.factories import UserFactory, InstructorFactory, StaffFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class InlineAnalyticsTest(ModuleStoreTestCase):
    """ unittest class """

    def setUp(self):
        super(InlineAnalyticsTest, self).setUp()
        self.user = UserFactory.create()
        self.factory = RequestFactory()
        self.course = CourseFactory.create(
            org="A",
            number="B",
            run="C",
        )
        self.staff = StaffFactory(course_key=self.course.id)
        self.instructor = InstructorFactory(course_key=self.course.id)

        analytics_data = {
            "module_id": "123",
            "question_types_by_part": "radio",
            "num_options_by_part": 6,
            "course_id": "A/B/C",
        }
        json_analytics_data = json.dumps(analytics_data)
        self.data = {"data": json_analytics_data}

    @override_settings(ANALYTICS_ANSWER_DIST_URL='dummy_url')
    def test_regular_user(self):

        request = self.factory.post('', self.data)
        request.user = self.user

        response = get_analytics_answer_dist(request)
        self.assertEquals(response.content, 'A problem has occurred retrieving the data, please report the problem.')

    def test_no_url(self):

        request = self.factory.post('', self.data)
        request.user = self.instructor

        response = get_analytics_answer_dist(request)
        self.assertEquals(response.content, 'A problem has occurred retrieving the data, please report the problem.')

    @override_settings(ANALYTICS_ANSWER_DIST_URL='dummy_url')
    @patch('urllib2.urlopen')
    @patch('courseware.views.process_analytics_answer_dist')
    def test_staff_and_url(self, mock_process_analytics, mock_requests):

        mock_resp = MagicMock()
        mock_read = MagicMock(return_value="{}")
        mock_resp.read = mock_read
        mock_requests.return_value = mock_resp

        factory = self.factory
        request = factory.post('', self.data)
        request.user = self.staff

        mock_process_analytics.return_value = [{'dummy': 'dummy'}]
        response = get_analytics_answer_dist(request)
        self.assertEquals(response, [{'dummy': 'dummy'}])

    @override_settings(ANALYTICS_ANSWER_DIST_URL='dummy_url')
    @patch('urllib2.urlopen')
    @patch('courseware.views.process_analytics_answer_dist')
    def test_instructor_and_url(self, mock_process_analytics, mock_requests):

        mock_resp = MagicMock()
        mock_read = MagicMock(return_value="{}")
        mock_resp.read = mock_read
        mock_requests.return_value = mock_resp

        factory = self.factory
        request = factory.post('', self.data)
        request.user = self.instructor

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
                "variant": None,
                "created": "2014-10-15T101351",
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
                "variant": None,
                "created": "2014-10-15T101351",
            },
        ]

        question_types_by_part = {
            "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": "radio",
        }

        num_options_by_part = {
            "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": 4,
        }

        processed_data = {
            u"count_by_part": {
                u"i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": {
                    u"totalIncorrectCount": 7,
                    u"totalAttemptCount": 30,
                    u"totalCorrectCount": 23,
                },
            },
            u"data_by_part": {
                u"i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": [
                    {
                        u"count": 7,
                        u"value_id": u"choice_0",
                        u"correct": False,
                    },
                    {
                        u"count": 23,
                        u"value_id": u"choice_1",
                        u"correct": True,
                    },
                ]
            },
            u"message_by_part": {
            },
            u"last_update_date": u"Oct 15, 2014 at 10:13 UTC"
        }

        return_json = process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)
        self.maxDiff = None
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
                "variant": None,
                "created": "2014-10-15T101351",
            },
        ]

        question_types_by_part = {
            "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": "radio",
        }

        num_options_by_part = {
            "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": 4,
        }

        processed_data = {
            u"count_by_part": {
                u"i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": {
                    u"totalIncorrectCount": 7,
                    u"totalAttemptCount": 7,
                    u"totalCorrectCount": 0,
                },
            },
            u"data_by_part": {
                u"i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": [
                    {
                        u"count": 7,
                        u"value_id": u"choice_0",
                        u"correct": False,
                    },
                ]
            },
            u"message_by_part": {
            },
            u"last_update_date": u"Oct 15, 2014 at 10:13 UTC"
        }

        return_json = process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)
        self.maxDiff = None
        self.assertEquals(json.loads(return_json.content), processed_data)

    def test_process_analytics_answer_dist_variant(self):

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
                "variant": "123",
                "created": "2014-10-15T101351",
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
                "variant": None,
                "created": "2014-10-15T101351",
            },
        ]

        question_types_by_part = {
            "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": "radio",
        }

        num_options_by_part = {
            "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": 4,
        }

        processed_data = {
            u"count_by_part": {
                u"i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": {
                    u"totalIncorrectCount": 0,
                    u"totalAttemptCount": 23,
                    u"totalCorrectCount": 23,
                },
            },
            u"data_by_part": {
                u"i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": [
                    {
                        u"count": 23,
                        u"value_id": u"choice_1",
                        u"correct": True,
                    },
                ]
            },
            u"message_by_part": {
                u"i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": u"The analytics cannot be displayed for this question as randomization was set at one time."
            },
            u"last_update_date": u"Oct 15, 2014 at 10:13 UTC"
        }

        return_json = process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)
        self.maxDiff = None
        self.assertEquals(json.loads(return_json.content), processed_data)

    def test_process_analytics_answer_dist_radio(self):

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
                "variant": "123",
                "created": "2014-10-15T101351",
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
                "variant": None,
                "created": "2014-10-15T101351",
            },
        ]

        question_types_by_part = {
            "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": "radio",
        }

        num_options_by_part = {
            "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": 1,
        }

        processed_data = {
            u"count_by_part": {
            },
            u"data_by_part": {
            },
            u"message_by_part": {
                u"i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": u"The analytics cannot be displayed for this question as the number of rows returned did not match the question definition."
            },
            u"last_update_date": u"Oct 15, 2014 at 10:13 UTC"
        }

        return_json = process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)
        self.maxDiff = None
        self.assertEquals(json.loads(return_json.content), processed_data)

    def test_process_analytics_answer_dist_checkbox(self):

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
                "variant": "123",
                "created": "2014-10-15T101351",
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
                "variant": None,
                "created": "2014-10-15T101351",
            },
        ]

        question_types_by_part = {
            "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": "checkbox",
        }

        num_options_by_part = {
            "i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": 0,
        }

        processed_data = {
            u"count_by_part": {
            },
            u"data_by_part": {
            },
            u"message_by_part": {
                u"i4x-A-B-problem-f3ed0ba7f89445ee9a83541e1fc8a2f2_2_1": u"The analytics cannot be displayed for this question as the number of rows returned did not match the question definition."
            },
            u"last_update_date": u"Oct 15, 2014 at 10:13 UTC"
        }

        return_json = process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)
        self.maxDiff = None
        self.assertEquals(json.loads(return_json.content), processed_data)
