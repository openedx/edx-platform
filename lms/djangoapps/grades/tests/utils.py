"""
Utilities for grades related tests
"""
from contextlib import contextmanager
from mock import patch
from courseware.module_render import get_module
from courseware.model_data import FieldDataCache


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


def answer_problem(course, request, problem, score=1, max_value=1):
    """
    Records an answer for the given problem.

    Arguments:
        course (Course): Course object, the course the required problem is in
        request (Request): request Object
        problem (xblock): xblock object, the problem to be answered
        score (float): The new score for the problem
        max_value (float): The new maximum score for the problem
    """

    user = request.user
    grade_dict = {'value': score, 'max_value': max_value, 'user_id': user.id}
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id,
        user,
        course,
        depth=2
    )
    module = get_module(
        user,
        request,
        problem.location,
        field_data_cache,
    )
    module.runtime.publish(problem, 'grade', grade_dict)
