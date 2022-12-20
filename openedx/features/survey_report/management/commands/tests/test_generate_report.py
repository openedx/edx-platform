"""
Test for generate_report command.
"""

from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from openedx.features.survey_report.models import SurveyReport


class GenerateReportTest(TestCase):
    """
    Test for generate_report command.
    """

    @mock.patch('openedx.features.survey_report.api.get_report_data')
    def test_generate_report(self, mock_get_report_data):
        """
        Test that generate_report command creates a survey report.
        """
        report_test_data = {
            'courses_offered': 1,
            'learners': 2,
            'registered_learners': 3,
            'generated_certificates': 4,
            'enrollments': 5,
            'extra_data': {'extra': 'data'},
        }
        mock_get_report_data.return_value = report_test_data
        out = StringIO()
        call_command('generate_report', no_send=True, stdout=out)

        survey_report = SurveyReport.objects.last()

        assert survey_report.courses_offered == report_test_data['courses_offered']
        assert survey_report.learners == report_test_data['learners']
        assert survey_report.registered_learners == report_test_data['registered_learners']
        assert survey_report.generated_certificates == report_test_data['generated_certificates']
        assert survey_report.enrollments == report_test_data['enrollments']
        assert survey_report.extra_data == report_test_data['extra_data']
