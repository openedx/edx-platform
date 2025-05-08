"""
Tests for the Python APIs exposed by the Progress API of the Course Home API app.
"""

from unittest.mock import patch

from django.test import TestCase

from lms.djangoapps.course_home_api.progress.api import calculate_progress_for_learner_in_course


class ProgressApiTests(TestCase):
    """
    Tests for the progress calculation functions.
    """

    @patch("lms.djangoapps.course_home_api.progress.api.get_course_blocks_completion_summary")
    def test_calculate_progress_for_learner_in_course(self, mock_get_summary):
        """
        A test to verify functionality of the function under test.
        """
        mock_get_summary.return_value = {
            "complete_count": 5,
            "incomplete_count": 2,
            "locked_count": 1,
        }

        expected_data = {
            "complete_count": 5,
            "incomplete_count": 2,
            "locked_count": 1,
            "total_count": 8,
            "complete_percentage": 0.62,
            "locked_percentage": 0.12,
            "incomplete_percentage": 0.26,
        }

        results = calculate_progress_for_learner_in_course("some_course", "some_user")
        assert mock_get_summary.called_once_with("some_course", "some_user")
        assert results == expected_data

    @patch("lms.djangoapps.course_home_api.progress.api.get_course_blocks_completion_summary")
    def test_handle_division_by_zero(self, mock_get_summary):
        """
        A test to verify that we're avoiding division-by-zero errors if the total number of units is 0.
        """
        mock_get_summary.return_value = {
            "complete_count": 0,
            "incomplete_count": 0,
            "locked_count": 0,
        }

        expected_data = {
            "complete_count": 0,
            "incomplete_count": 0,
            "locked_count": 0,
            "total_count": 0,
            "complete_percentage": 0.0,
            "locked_percentage": 0.0,
            "incomplete_percentage": 0.0,
        }

        results = calculate_progress_for_learner_in_course("some_course", "some_user")
        assert mock_get_summary.called_once_with("some_course", "some_user")
        assert results == expected_data

    @patch("lms.djangoapps.course_home_api.progress.api.get_course_blocks_completion_summary")
    def test_calculate_progress_for_learner_in_course_summary_empty(self, mock_get_summary):
        """
        A test to verify functionality of the function under test if a block summary is not received.
        """
        mock_get_summary.return_value = {}

        results = calculate_progress_for_learner_in_course("some_course", "some_user")
        assert not results
