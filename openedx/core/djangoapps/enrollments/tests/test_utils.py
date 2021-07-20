"""
Tests for enrollment utils
"""
import unittest
from unittest.mock import patch

from openedx.core.djangoapps.enrollments.utils import add_user_to_course_cohort


class EnrollmentUtilsTest(unittest.TestCase):
    """
    Enrollment utils test cases
    """
    @patch("openedx.core.djangoapps.enrollments.utils.add_user_to_cohort")
    @patch("openedx.core.djangoapps.enrollments.utils.get_cohort_by_name")
    def test_adds_user_to_cohort(self, mock_get_cohort_by_name, mock_add_user_to_cohort):
        user = {}
        mock_get_cohort_by_name.return_value = "a_cohort"

        add_user_to_course_cohort("a_cohort", "a_course_id", user)
        assert mock_add_user_to_cohort.call_count == 1

    @patch("openedx.core.djangoapps.enrollments.utils.add_user_to_cohort")
    @patch("openedx.core.djangoapps.enrollments.utils.get_cohort_by_name")
    def test_does_not_add_user_to_cohort(self, mock_get_cohort_by_name, mock_add_user_to_cohort):
        user = {}
        mock_get_cohort_by_name.return_value = "a_cohort"

        add_user_to_course_cohort(None, "a_course_id", user)
        assert mock_add_user_to_cohort.call_count == 0
