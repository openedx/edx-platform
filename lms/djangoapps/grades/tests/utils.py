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


@contextmanager
def mock_get_score(earned=0, possible=1):
    """
    Mocks the get_score function to return a valid grade.
    """
    with patch('lms.djangoapps.grades.new.subsection_grade.get_score') as mock_score:
        mock_score.return_value = (earned, possible)
        yield mock_score
