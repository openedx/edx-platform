"""
Tests to check if `update_is_prerequisite_courses_passed` command actually updates the `is_prerequisite_courses_passed`
flag in Application Hub for each eligible user
"""
import pytest
from django.core.management import call_command

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.grades.models import PersistentCourseGrade
from openedx.adg.lms.applications.management.commands import update_is_prerequisite_courses_passed as command_module
from openedx.adg.lms.applications.tests.constants import PROGRAM_PRE_REQ
from openedx.adg.lms.applications.tests.factories import ApplicationHubFactory


@pytest.mark.django_db
def test_command_update_is_prerequisite_courses_passed_with_no_prerequisites():
    """
    Test to check if management command issues a system exit upon no prerequisites
    """
    with pytest.raises(SystemExit):
        call_command('update_is_prerequisite_courses_passed')


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [(1, PROGRAM_PRE_REQ)], indirect=True)
@pytest.mark.usefixtures('prereq_course_groups')
def test_command_update_is_prerequisite_courses_no_users_to_be_checked_for_update(mocker):
    """
    Test to check if management command issues a system exit when given an empty list of users to be checked for update
    """
    mocker.patch(
        'openedx.adg.lms.applications.helpers.get_users_with_active_enrollments_from_course_groups',
        return_value=[]
    )

    with pytest.raises(SystemExit):
        call_command('update_is_prerequisite_courses_passed')


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [(1, PROGRAM_PRE_REQ)], indirect=True)
@pytest.mark.parametrize('eligible_users_count', (2, 4, 5))
def test_get_users_eligible_for_update(prereq_course_groups, eligible_users_count):
    """
    Assert that only users who have passed the program prerequisite courses are returned
    """
    multilingual_courses = prereq_course_groups[0].multilingual_courses.open_multilingual_courses()
    users = UserFactory.create_batch(5)

    for i in range(eligible_users_count):
        PersistentCourseGrade.update_or_create(
            user_id=users[i].id,
            course_id=multilingual_courses[0].course.id,
            percent_grade=80,
            letter_grade='A',
            passed=True,
        )

    command = command_module.Command()
    eligible_users = command.get_users_eligible_for_update(users)
    assert len(eligible_users) == eligible_users_count


@pytest.mark.django_db
@pytest.mark.parametrize(
    'is_written_application_completed, is_prerequisite_courses_passed, expected_result',
    [
        (True, False, 1), (True, True, 0), (False, True, 0), (False, False, 0),
    ]
)
def test_get_user_ids_with_program_pre_reqs_not_marked_as_passed(
    is_written_application_completed, is_prerequisite_courses_passed, expected_result
):
    """
    Assert that only those user ids are returned whose application is completed but prereqs are not passed
    """
    ApplicationHubFactory(
        is_written_application_completed=is_written_application_completed,
        is_prerequisite_courses_passed=is_prerequisite_courses_passed,
    )
    command = command_module.Command()
    filtered_users = command.get_user_ids_with_program_pre_reqs_not_marked_as_passed()

    assert len(filtered_users) == expected_result
