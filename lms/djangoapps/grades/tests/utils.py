"""
Utilities for grades related tests
"""
from contextlib import contextmanager
from mock import patch


@contextmanager
def mock_passing_grade(grade_pass='Pass', percent=0.75):
    """
    Mock the grading function to always return a passing grade.
    """
    with patch('lms.djangoapps.grades.course_grades.summary') as mock_grade:
        mock_grade.return_value = {'grade': grade_pass, 'percent': percent}
        yield
