"""
Tests to check if `update_is_prerequisite_courses_passed` command actually updates the `is_prerequisite_courses_passed`
flag in Application Hub for each eligible user
"""
import logging
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone
from mock import Mock

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from openedx.adg.lms.applications.management.commands import update_is_prerequisite_courses_passed as command_module
from openedx.adg.lms.applications.tests.factories import (
    ApplicationHubFactory,
    MultilingualCourseFactory,
    MultilingualCourseGroupFactory
)


@pytest.fixture(name='prereq_course_groups')
def create_prerequisite_course_group_with_course_enrollment(request):
    """
    This fixture creates courses equal to the size of the boolean list and makes them prerequisite depending on the
    boolean value at each index
    """
    course_groups = MultilingualCourseGroupFactory.create_batch(request.param)

    for course_group in course_groups:
        now = timezone.now()
        # Open prereq courses
        MultilingualCourseFactory.create_batch(
            2, course__start_date=now, course__end_date=now + timedelta(days=1), multilingual_course_group=course_group
        )
        # Ended prereq course
        MultilingualCourseFactory(
            course__start_date=now + timedelta(days=2), course__end_date=now, multilingual_course_group=course_group
        )
    return course_groups


def get_user_ids(users):
    """
    Get list of ids for list of users
    """
    return [user.id for user in users]


@pytest.mark.django_db
def test_command_update_is_prerequisite_courses_passed_with_no_prerequisites():
    """
    Test to check if management command issues a system exits upon no prerequisites
    """
    with pytest.raises(SystemExit):
        call_command('update_is_prerequisite_courses_passed')


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [1], indirect=True)
@pytest.mark.usefixtures('prereq_course_groups')
def test_command_update_is_prerequisite_courses_no_users_to_be_checked_for_update(mocker):
    """
    Test to check if management command issues a system exits upon empty list of users to be checked for update
    """
    mocker.patch.object(command_module.Command, 'get_minimal_users_to_be_checked_for_update', return_value=None)

    with pytest.raises(SystemExit):
        call_command('update_is_prerequisite_courses_passed')


@pytest.mark.django_db
def test_get_minimal_users_to_be_checked_for_update(mocker):
    """
    Assert that common user ids are returned which means users with valid enrollment in each course group
    """
    user_ids = [100, 200, 300, 400, 500]
    side_effect_list = [[100, 200, 300, 500], [200, 300, 500], [200, 300]]

    prereq_course_groups = [Mock(), Mock(), Mock()]
    mocker.patch.object(
        command_module.Command, 'get_users_with_pre_reqs_not_marked_as_passed', return_value=user_ids
    )
    mocker.patch.object(
        command_module.Command, 'get_users_with_active_course_enrollments', side_effect=side_effect_list
    )

    command = command_module.Command()
    filtered_user_ids = command.get_minimal_users_to_be_checked_for_update(prereq_course_groups)

    assert filtered_user_ids == [200, 300]


@pytest.mark.django_db
def test_filter_user_by_application_passed_courses():
    """
    Assert that only users with applications hub association and incomplete prereq courses are returned
    """
    incomplete_application = ApplicationHubFactory(is_prerequisite_courses_passed=False)
    ApplicationHubFactory(is_prerequisite_courses_passed=True)

    command = command_module.Command()
    filtered_user_ids = command.get_users_with_pre_reqs_not_marked_as_passed()

    assert sorted(filtered_user_ids) == [incomplete_application.user.id]


@pytest.mark.django_db
def test_get_users_with_pre_reqs_not_marked_as_passed_no_application_hub():
    """
    Assert that users without applications hub are returned
    """
    users = UserFactory.create_batch(2)

    command = command_module.Command()
    filtered_user_ids = command.get_users_with_pre_reqs_not_marked_as_passed()

    assert sorted(filtered_user_ids) == get_user_ids(users)


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [1], indirect=True)
def test_get_users_with_active_course_enrollments_enroll_users_in_open_courses(prereq_course_groups):
    """
    Assert that users actively enrolled in open courses are filtered and returned
    """
    users = UserFactory.create_batch(3)
    user_ids = get_user_ids(users)
    prereq_course_group = prereq_course_groups.pop()
    open_course_keys = prereq_course_group.open_multilingual_course_keys()
    CourseEnrollmentFactory(user=users[0], course_id=open_course_keys[0], is_active=True)
    CourseEnrollmentFactory(user=users[0], course_id=open_course_keys[1], is_active=True)
    CourseEnrollmentFactory(user=users[1], course_id=open_course_keys[0], is_active=True)

    command = command_module.Command()
    filtered_user_ids = command.get_users_with_active_course_enrollments(user_ids, prereq_course_group)

    assert sorted(filtered_user_ids) == [user_ids[0], user_ids[1]]


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [1], indirect=True)
def test_get_users_with_active_course_enrollments_ignore_inactive_enrollment_in_open_course(prereq_course_groups):
    """
    Assert that user enrolled in inactive courses are ignore
    """
    users = UserFactory.create_batch(3)
    user_ids = get_user_ids(users)
    prereq_course_group = prereq_course_groups.pop()
    open_course_keys = prereq_course_group.open_multilingual_course_keys()
    CourseEnrollmentFactory(user=users[0], course_id=open_course_keys[0], is_active=False)

    command = command_module.Command()
    users = command.get_users_with_active_course_enrollments(user_ids, prereq_course_group)

    assert users.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [1], indirect=True)
def test_get_users_with_active_course_enrollments_ignore_enrollment_in_closed_course(prereq_course_groups):
    """
    Assert that user enrolled in closed courses are ignore
    """
    users = UserFactory.create_batch(3)
    user_ids = get_user_ids(users)
    prereq_course_group = prereq_course_groups.pop()
    closed_courses = prereq_course_group.multilingual_courses(
        manager='objects'
    ).filter(course__end_date__lt=timezone.now())
    CourseEnrollmentFactory(user=users[0], course_id=closed_courses[0].course_id, is_active=True)

    command = command_module.Command()
    users = command.get_users_with_active_course_enrollments(user_ids, prereq_course_group)

    assert users.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [2], indirect=True)
def test_check_users_for_application_update_successfully(mocker, prereq_course_groups):
    """
    Assert that all users are check for application update
    """
    users = UserFactory.create_batch(2)
    user_ids = get_user_ids(users)
    mock_check_passed_prereq_courses = mocker.patch.object(
        command_module.Command, 'check_passed_prereq_courses_and_update_application_hub'
    )

    command = command_module.Command()
    command.check_users_for_application_update(user_ids, prereq_course_groups)

    calls = [mocker.call(users[0], prereq_course_groups), mocker.call(users[1], prereq_course_groups)]
    mock_check_passed_prereq_courses.assert_has_calls(calls)


@pytest.mark.django_db
def test_check_users_for_application_update_empty_user_list(mocker):
    """
    Assert that no user is check for application update
    """
    mock_check_passed_prereq_courses = mocker.patch.object(
        command_module.Command, 'check_passed_prereq_courses_and_update_application_hub'
    )

    command = command_module.Command()
    command.check_users_for_application_update([], mocker.ANY)

    assert not mock_check_passed_prereq_courses.called


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [2], indirect=True)
def test_check_passed_prereq_courses_and_update_application_hub_all_passed(mocker, prereq_course_groups):
    """
    Assert that user have passed all prereq courses, if all course groups are passed
    """
    user = UserFactory()
    mocker.patch.object(command_module.Command, 'is_user_failed_in_course_group', side_effect=[False, False])
    mock_update_application_hub = mocker.patch.object(command_module.Command, 'update_application_hub')

    command = command_module.Command()
    command.check_passed_prereq_courses_and_update_application_hub(user, prereq_course_groups)

    mock_update_application_hub.assert_called_once_with(user)


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [2], indirect=True)
def test_check_passed_prereq_courses_and_update_application_hub_all_not_passed(mocker, caplog, prereq_course_groups):
    """
    Assert that user have not passed prereq courses, if all course groups are not passed
    """
    user = UserFactory()
    mocker.patch.object(command_module.Command, 'is_user_failed_in_course_group', side_effect=[False, True])

    caplog.set_level(logging.INFO)
    command = command_module.Command()
    command.check_passed_prereq_courses_and_update_application_hub(user, prereq_course_groups)

    assert '{username} has not yet passed'.format(username=user.username) in caplog.messages[0]


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [1], indirect=True)
@pytest.mark.parametrize("course_status,expected", [
    pytest.param([None, Mock(passed=True), Mock(passed=True)], False, id='only_one_course_passed'),
    pytest.param([None, Mock(passed=False), Mock(passed=True)], True, id='only_ended_course_passed')
])
def test_is_user_failed_in_course_group(mocker, prereq_course_groups, course_status, expected):
    """
    Assert that for a given course group of three courses (2 open, 1 ended), user pass prereq course
    when one of the open course is passed.
    """
    mock_course_grade_factory_read = mocker.patch.object(
        command_module.CourseGradeFactory, '_read', side_effect=course_status
    )

    command = command_module.Command()
    is_failed = command.is_user_failed_in_course_group(UserFactory(), prereq_course_groups.pop())

    assert is_failed is expected
    assert mock_course_grade_factory_read.call_count == 2


@pytest.mark.django_db
def test_update_application_hub_successfully(mocker, caplog):
    """
    Assert that flag is successfully updated in application hub model
    """
    user = UserFactory()
    ApplicationHubFactory(user=user)
    mocker_set_is_prerequisite_courses_passed = mocker.patch.object(
        command_module.ApplicationHub, 'set_is_prerequisite_courses_passed'
    )

    caplog.set_level(logging.INFO)
    command = command_module.Command()
    command.update_application_hub(user)

    assert mocker_set_is_prerequisite_courses_passed.call_count == 1
    assert '{username} has successfully'.format(username=user.username) in caplog.messages[0]
