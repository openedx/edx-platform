"""
Tests to check if `update_is_bu_prerequisite_courses_passed` command actually updates the
`is_bu_prerequisite_courses_passed` flag in Application Hub for each eligible user
"""
from unittest.mock import ANY

import pytest
from django.core.management import call_command

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.grades.models import PersistentCourseGrade
from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.lms.applications.management.commands import update_is_bu_prerequisite_courses_passed as command_module
from openedx.adg.lms.applications.tests.constants import BUSINESS_LINE_PRE_REQ
from openedx.adg.lms.applications.tests.factories import ApplicationHubFactory, UserApplicationFactory


@pytest.mark.django_db
def test_command_update_is_bu_prerequisite_courses_passed_with_no_prerequisites():
    """
    Test to check if management command issues a system exit upon no prerequisites
    """
    with pytest.raises(SystemExit):
        call_command('update_is_bu_prerequisite_courses_passed')


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [(1, BUSINESS_LINE_PRE_REQ)], indirect=True)
@pytest.mark.usefixtures('prereq_course_groups')
def test_command_update_is_bu_prerequisite_courses_no_users_to_be_checked_for_update(mocker):
    """
    Test to check if management command issues a system exit when given an empty list of users to be checked for update
    """
    mocker.patch(
        'openedx.adg.lms.applications.helpers.get_users_with_active_enrollments_from_course_groups',
        return_value=[]
    )

    with pytest.raises(SystemExit):
        call_command('update_is_bu_prerequisite_courses_passed')


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [(1, BUSINESS_LINE_PRE_REQ)], indirect=['prereq_course_groups'])
@pytest.mark.parametrize('eligible_users_count', (2, 4, 5))
def test_get_users_eligible_for_update(prereq_course_groups, eligible_users_count):
    """
    Assert that only users who have passed the business line and common business line
    prerequisite courses are returned
    """
    multilingual_courses = prereq_course_groups[0].multilingual_courses.open_multilingual_courses()

    user_applications = UserApplicationFactory.create_batch(5)
    users = [users_application.user for users_application in user_applications]

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
    'is_written_application_completed, is_prerequisite_courses_passed, is_bu_prerequisite_courses_passed, exp_result',
    [
        (True, True, True, 0),
        (True, True, False, 1),
        (True, False, True, 0),
        (True, False, False, 0),
        (False, True, True, 0),
        (False, True, False, 0),
        (False, False, True, 0),
        (False, False, False, 0),
    ]
)
def test_get_user_ids_with_bu_pre_reqs_not_marked_as_passed(
    is_written_application_completed,
    is_prerequisite_courses_passed,
    is_bu_prerequisite_courses_passed,
    exp_result
):
    """
    Assert that only those user ids are returned whose application is completed and program prereqs are passed
    but business line and common business line prereqs are not passed
    """
    ApplicationHubFactory(
        is_written_application_completed=is_written_application_completed,
        is_prerequisite_courses_passed=is_prerequisite_courses_passed,
        is_bu_prerequisite_courses_passed=is_bu_prerequisite_courses_passed,
    )
    command = command_module.Command()
    filtered_users = command.get_user_ids_with_bu_pre_reqs_not_marked_as_passed()

    assert len(filtered_users) == exp_result


@pytest.mark.django_db
def test_send_application_submission_emails(mocker):
    """
    Assert that application submission email is sent to given list of users
    """
    users = UserFactory.create_batch(5)
    user_emails = [user.email for user in users]

    mocked_task_send_mandrill_email = mocker.patch('openedx.adg.lms.applications.helpers.task_send_mandrill_email')

    command = command_module.Command()
    command.send_application_submission_emails(users)

    mocked_task_send_mandrill_email.delay.assert_called_once_with(
        MandrillClient.APPLICATION_SUBMISSION_CONFIRMATION, user_emails, ANY
    )
