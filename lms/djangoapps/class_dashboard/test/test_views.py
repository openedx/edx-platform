from mock import Mock, patch

from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import simplejson

from class_dashboard import views


class TestViews(TestCase):

    def setUp(self):
        self.request_factory = RequestFactory()
        self.request = self.request_factory.get('')
        self.request.user = None
        self.simple_data = {'test': 'test'}

    @patch('class_dashboard.dashboard_data.get_d3_problem_attempt_distribution')
    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_all_problem_attempt_distribution_has_access(self, has_access, data_method):
        """
        Test returns proper value when have proper access
        """
        has_access.return_value = True

        data_method.return_value = self.simple_data

        response = views.all_problem_attempt_distribution(self.request, 'test/test/test')

        self.assertEqual(simplejson.dumps(self.simple_data), response.content)

    @patch('class_dashboard.dashboard_data.get_d3_problem_grade_distribution')
    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_all_problem_grade_distribution_has_access(self, has_access, data_method):
        """
        Test returns proper value when have proper access
        """
        has_access.return_value = True

        data_method.return_value = self.simple_data

        response = views.all_problem_grade_distribution(self.request, 'test/test/test')

        self.assertEqual(simplejson.dumps(self.simple_data), response.content)

    @patch('class_dashboard.dashboard_data.get_d3_sequential_open_distribution')
    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_all_sequential_open_distribution_has_access(self, has_access, data_method):
        """
        Test returns proper value when have proper access
        """
        has_access.return_value = True

        data_method.return_value = self.simple_data

        response = views.all_sequential_open_distribution(self.request, 'test/test/test')

        self.assertEqual(simplejson.dumps(self.simple_data), response.content)

    @patch('class_dashboard.dashboard_data.get_d3_section_grade_distribution')
    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_section_problem_grade_distribution_has_access(self, has_access, data_method):
        """
        Test returns proper value when have proper access
        """
        has_access.return_value = True

        data_method.return_value = self.simple_data

        response = views.section_problem_grade_distribution(self.request, 'test/test/test', '1')

        self.assertEqual(simplejson.dumps(self.simple_data), response.content)
