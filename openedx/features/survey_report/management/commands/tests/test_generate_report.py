"""
Test for generate_report command.
"""

from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings

from openedx.features.survey_report.models import SurveyReport


class GenerateReportTest(TestCase):
    """
    Test for generate_report command.
    """
    @override_settings(SURVEY_REPORT_EXTRA_DATA={'extra_data': 'extra_data'})
    @mock.patch('openedx.features.survey_report.queries.get_course_enrollments')
    @mock.patch('openedx.features.survey_report.queries.get_generated_certificates')
    @mock.patch('openedx.features.survey_report.queries.get_learners_registered')
    @mock.patch('openedx.features.survey_report.queries.get_currently_learners')
    @mock.patch('openedx.features.survey_report.queries.get_unique_courses_offered')
    def test_generate_report(self, mock_get_unique_courses_offered, mock_get_currently_learners,
                             mock_get_learners_registered, mock_get_generated_certificates,
                             mock_get_course_enrollments):
        """
        Test that generate_report command creates a survey report.
        """
        mock_get_unique_courses_offered.return_value = 1
        mock_get_currently_learners.return_value = 2
        mock_get_learners_registered.return_value = 3
        mock_get_generated_certificates.return_value = 4
        mock_get_course_enrollments.return_value = 5
        out = StringIO()
        call_command('generate_report', stdout=out)

        survey_report = SurveyReport.objects.last()
        assert survey_report.courses_offered == 1
        assert survey_report.learners == 2
        assert survey_report.registered_learners == 3
        assert survey_report.generated_certificates == 4
        assert survey_report.enrollments == 5
        assert survey_report.extra_data == {'extra_data': 'extra_data'}
