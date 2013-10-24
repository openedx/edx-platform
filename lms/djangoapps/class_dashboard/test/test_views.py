from mock import Mock, patch

from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import simplejson

from class_dashboard import views
from student.tests.factories import AdminFactory


class TestViews(TestCase):

    def setUp(self):

        self.request_factory = RequestFactory()
        self.request = self.request_factory.get('')
        self.request.user = None
        self.simple_data = {'test': 'test'}

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
        
    @patch('class_dashboard.dashboard_data.get_d3_problem_grade_distribution')
    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_all_problem_grade_distribution_no_access(self, has_access, data_method):
        """
        Test for no access
        """
        has_access.return_value = False
        response = views.section_problem_grade_distribution(self.request, 'test/test/test', '1')

        self.assertEqual("{\"error\": \"Access Denied: User does not have access to this course\'s data\"}", response.content)

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

    @patch('class_dashboard.dashboard_data.get_d3_sequential_open_distribution')
    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_all_sequential_open_distribution_no_access(self, has_access, data_method):
        """
        Test for no access
        """
        has_access.return_value = False
        response = views.section_problem_grade_distribution(self.request, 'test/test/test', '1')

        self.assertEqual("{\"error\": \"Access Denied: User does not have access to this course\'s data\"}", response.content)

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
        
    @patch('class_dashboard.dashboard_data.get_d3_section_grade_distribution')
    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_section_problem_grade_distribution_no_access(self, has_access, data_method):
        """
        Test for no access
        """
        has_access.return_value = False
        response = views.section_problem_grade_distribution(self.request, 'test/test/test', '1')

        self.assertEqual("{\"error\": \"Access Denied: User does not have access to this course\'s data\"}", response.content)
