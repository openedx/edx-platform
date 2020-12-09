"""
Tests for all the models in applications app.
"""
from datetime import date

import pytest

from student.tests.factories import UserFactory

from .constants import USERNAME
from .factories import ApplicationHubFactory


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
    ([], '0%'),
    (['is_prerequisite_courses_passed'], '50%'),
    (['is_written_application_completed'], '50%'),
    (['is_prerequisite_courses_passed', 'is_written_application_completed'], '100%')
])
def test_percentage_of_objectives_completed_in_application_hub(objectives_completed,
                                                               expected_return_value,
                                                               application_hub):
    """
    Test if the `percentage_of_objectives_completed` property is working as expected for all possible cases.
    """
    mark_objectives_complete(application_hub, objectives_completed)
    assert application_hub.percentage_of_objectives_completed == expected_return_value


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
def test_are_application_pre_reqs_completed_in_application_hub(objectives_completed,
                                                               expected_return_value,
                                                               application_hub):
    """
    Test if the `are_application_pre_reqs_completed` property is working as expected for all possible cases.
    """
    mark_objectives_complete(application_hub, objectives_completed)
    assert application_hub.are_application_pre_reqs_completed() is expected_return_value
