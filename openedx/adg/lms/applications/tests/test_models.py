"""
Tests for all the models in applications app.
"""
from datetime import date

import mock
import pytest

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.grades.api import CourseGradeFactory
from openedx.adg.lms.applications.constants import CourseScore
from openedx.adg.lms.applications.models import UserApplication
from openedx.core.lib.grade_utils import round_away_from_zero

from .constants import USERNAME
from .factories import ApplicationHubFactory, PrerequisiteCourseFactory, UserApplicationFactory


@pytest.mark.django_db
@pytest.fixture(name='application_hub')
def application_hub_fixture():
    """
    Create an ApplicationHub object for the specified test user.

    Returns:
        ApplicationHub object
    """
    user = UserFactory(username=USERNAME)
    return ApplicationHubFactory(user=user)


@pytest.mark.django_db
def test_set_is_prerequisite_courses_passed_in_application_hub(application_hub):
    """
    Test if the is_prerequisite_courses_passed is being set correctly by the model method.
    """
    application_hub.set_is_prerequisite_courses_passed()
    assert ApplicationHubFactory(user=application_hub.user).is_prerequisite_courses_passed


def mark_objectives_complete(application_hub, objectives_completed):
    """
    Mark the given objectives complete in the model object

    Args:
        objectives_completed(list): List of strings, each representing a model field i.e objective
        application_hub(ApplicationHub): The model object on which these objectives are to be set

    Returns:
        None
    """
    for objective in objectives_completed:
        setattr(application_hub, objective, True)


@pytest.mark.django_db
@pytest.mark.parametrize('objectives_completed,expected_return_value', [
    ([], 0.0),
    (['is_prerequisite_courses_passed'], 0.5),
    (['is_written_application_completed'], 0.5),
    (['is_prerequisite_courses_passed', 'is_written_application_completed'], 1.0)
])
def test_progress_of_objectives_completed_in_float_in_application_hub(
    objectives_completed, expected_return_value, application_hub
):
    """
    Test if the `percentage_of_objectives_completed` property is working as expected for all possible cases.
    """
    mark_objectives_complete(application_hub, objectives_completed)
    assert application_hub.progress_of_objectives_completed_in_float == expected_return_value


@pytest.mark.django_db
def test_submit_application_for_current_date_in_application_hub(application_hub):
    """
    Test if the `submit_application_for_current_date` model method works as expected.
    """
    application_hub.submit_application_for_current_date()
    user_application_hub = ApplicationHubFactory(user=application_hub.user)
    assert user_application_hub.is_application_submitted
    assert user_application_hub.submission_date == date.today()


@pytest.mark.django_db
@pytest.mark.parametrize('objectives_completed,expected_return_value', [
    ([], False),
    (['is_prerequisite_courses_passed'], False),
    (['is_written_application_completed'], False),
    (['is_prerequisite_courses_passed', 'is_written_application_completed'], True)
])
def test_are_application_pre_reqs_completed_in_application_hub(
    objectives_completed, expected_return_value, application_hub
):
    """
    Test if the `are_application_pre_reqs_completed` property is working as expected for all possible cases.
    """
    mark_objectives_complete(application_hub, objectives_completed)
    assert application_hub.are_application_pre_reqs_completed() is expected_return_value


@pytest.mark.django_db
def test_user_application_string_representation(user_application):
    """
    Test that the string representation of a UserApplication object translates to the the full name of the applicant.
    """
    expected_str = user_application.user.profile.name
    actual_str = user_application.__str__()

    assert expected_str == actual_str


@pytest.mark.parametrize('percent', [0.9250, 0.7649])
@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.models.CourseGradeFactory.read')
def test_prereq_course_scores(mock_read, user_application, percent):
    """
    Test that the `prereq_course_scores` property returns the correct prerequisite course names and respective scores of
    the applicant in those courses, in the correct format.
    """
    test_course_1 = PrerequisiteCourseFactory().course
    test_course_2 = PrerequisiteCourseFactory().course

    course_grade = CourseGradeFactory()
    course_grade.percent = percent

    mock_read.return_value = course_grade

    score = int(round_away_from_zero(course_grade.percent * 100))
    course_score_1 = CourseScore(test_course_1.display_name, score)
    course_score_2 = CourseScore(test_course_2.display_name, score)

    expected_prereq_course_scores = [course_score_1, course_score_2]
    actual_prereq_course_scores = user_application.prereq_course_scores

    assert expected_prereq_course_scores == actual_prereq_course_scores


@pytest.mark.django_db
def test_education_string_representation(education):
    """
    Test that the string representation of an Education object is an empty string.
    """
    expected_str = ''
    actual_str = education.__str__()

    assert expected_str == actual_str


@pytest.mark.django_db
def test_work_experience_string_representation(work_experience):
    """
    Test that the string representation of a WorkExperience object is an empty string.
    """
    expected_str = ''
    actual_str = work_experience.__str__()

    assert expected_str == actual_str


@pytest.mark.django_db
def test_submitted_applications_manager():
    """
    Test that the SubmittedApplicationsManager returns only submitted applications.
    """
    user_application_1 = UserApplicationFactory()
    user_application_2 = UserApplicationFactory()

    application_hub_1 = ApplicationHubFactory()
    application_hub_1.user = user_application_1.user
    application_hub_1.is_application_submitted = True
    application_hub_1.save()

    application_hub_2 = ApplicationHubFactory()
    application_hub_2.user = user_application_2.user
    application_hub_2.save()

    expected_applications = [user_application_1]
    actual_applications = list(UserApplication.submitted_applications.all())

    assert expected_applications == actual_applications
