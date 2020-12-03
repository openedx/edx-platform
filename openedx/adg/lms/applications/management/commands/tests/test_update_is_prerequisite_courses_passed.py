"""
Tests to check if `update_is_prerequisite_courses_passed` command actually updates the `is_prerequisite_courses_passed`
flag in Application Hub for each eligible user
"""
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone
from mock import Mock

from openedx.adg.common.course_meta.tests.factories import CourseMetaFactory
from openedx.adg.lms.applications.management.commands import update_is_prerequisite_courses_passed as command_module
from openedx.adg.lms.applications.test.factories import ApplicationHubFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory


@pytest.fixture(name='create_users')
def create_users_in_batch(request):
    """
    This fixture creates users in batch based on the size sent in parameters
    """
    return UserFactory.create_batch(size=request.param)


@pytest.fixture(name='create_courses')
def create_prerequisite_and_regular_courses(request):
    """
    This fixture creates courses equal to the size of the boolean list and makes them prerequisite depending on the
    boolean value at each index
    """
    courses = list()
    prereq_courses = list()

    for is_prereq in request.param:
        course = CourseOverviewFactory(
            end_date=timezone.now() + timedelta(days=1),
            start_date=timezone.now(),
        )

        if is_prereq:
            CourseMetaFactory(course=course, is_prereq=is_prereq)
            prereq_courses.append(course)

        courses.append(course)

    return courses, prereq_courses


@pytest.fixture(name='enroll_users')
def create_active_and_inactive_enrollments(request, create_users, create_courses):
    """
    This fixture enrolls a user into courses sent by the `create_users` and `create_courses` fixtures respectively and
    makes the enrollments active/inactive depending on the boolean value at each index of the list sent as a parameter
    """
    activations = request.param
    courses, prerequisites = create_courses
    user = create_users.pop()

    for i, is_active in enumerate(activations):
        CourseEnrollmentFactory(
            course_id=courses[i].id,
            user=user,
            is_active=is_active
        )

    return prerequisites, user


@pytest.mark.django_db
@pytest.mark.parametrize('create_users', [1], indirect=True)
@pytest.mark.parametrize('create_courses', [[True]], indirect=True)
@pytest.mark.parametrize('enroll_users, expected_result', [([False], 0), ([True], 1)], indirect=['enroll_users'],
                         ids=['enrolled', 'not_enrolled'])
def test_get_minimal_users_to_be_checked_for_update_for_active_and_inactive_enrollments(enroll_users, expected_result):
    """
    Test to check that an inactive enrollment is not counted and active enrollment is counted while calculating minimal
    users
    """
    prerequisites, _ = enroll_users

    command = command_module.Command()
    minimal_users = command.get_minimal_users_to_be_checked_for_update(prerequisites)

    assert minimal_users.count() == expected_result


@pytest.mark.django_db
@pytest.mark.parametrize('create_courses', [[True]], indirect=True)
def test_get_minimal_users_to_be_checked_for_update_with_no_users_enrolled_in_prerequisite(create_courses):
    """
    Test to check that a user not enrolled in prerequisite is not counted while calculating minimal users
    """
    _, prerequisites = create_courses

    command = command_module.Command()
    minimal_users = command.get_minimal_users_to_be_checked_for_update(prerequisites)

    assert minimal_users.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize('create_users', [2], indirect=True)
@pytest.mark.parametrize('create_courses', [[True, True, False]], indirect=True)
@pytest.mark.parametrize('enroll_users', [[True, True], [True, True, False]], indirect=True,
                         ids=['2_prerequisites', '2_prerequisites_and_1_regular'])
def test_get_minimal_users_to_be_checked_for_update_with_active_enrollments_in_all_prerequisites(enroll_users):
    """
    Test to check that a user with two active enrollments in a total of two prerequisites and a user with two active
    enrollments in a total of two prerequisites and one enrollment in a regular course are counted but a user with no
    enrollments is not counted while calculating minimal users
    """
    prerequisites, user = enroll_users

    command = command_module.Command()
    minimal_users = command.get_minimal_users_to_be_checked_for_update(prerequisites)

    assert minimal_users.count() == 1
    assert minimal_users.first().username == user.username


@pytest.mark.django_db
@pytest.mark.parametrize('create_users', [2], indirect=True)
@pytest.mark.parametrize('create_courses', [[True, False, True], [True, True, True]], indirect=True,
                         ids=['1_out_of_2_prerequisites', '2_out_of_3_prerequisites'])
@pytest.mark.parametrize('enroll_users', [[True, True]], indirect=True)
def test_get_minimal_users_to_be_checked_for_update_with_active_enrollments_in_not_all_prerequisites(enroll_users):
    """
    Test to check that a user with one active enrollment in a total of two prerequisite and one enrollment in a
    regular course and a user with two active enrollments in a total of three prerequisite and a user with no
    enrollments are not counted while calculating minimal users
    """
    prerequisites, _ = enroll_users

    command = command_module.Command()
    minimal_users = command.get_minimal_users_to_be_checked_for_update(prerequisites)

    assert minimal_users.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize('create_users', [2], indirect=True)
@pytest.mark.parametrize('create_courses', [[True, True, True]], indirect=True)
@pytest.mark.parametrize('enroll_users', [[True, True]], indirect=True)
def test_get_minimal_users_to_be_checked_for_update_case_with_prerequisites_already_passed(enroll_users):
    """
    Test to check that a user already passed in prerequisites and a user with no enrollments are not counted while
    calculating minimal users
    """
    prerequisites, user = enroll_users

    user_application_hub = ApplicationHubFactory(user=user)
    user_application_hub.set_is_prerequisite_courses_passed()

    command = command_module.Command()
    minimal_users = command.get_minimal_users_to_be_checked_for_update(prerequisites)

    assert minimal_users.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize('course_grade, expected_result', [(None, True), (Mock(passed=True), False)],
                         ids=['failed', 'passed'])
def test_is_user_failed_in_course_for_a_failing_student_and_passed_student(mocker, course_grade, expected_result):
    """
    Test to check if the helper function `is_user_failed_in_course` returns True for a user failing in course and False
    for a user passed in course
    """
    mocker.patch.object(command_module.CourseGradeFactory, '_read', return_value=course_grade)

    command = command_module.Command()
    is_user_failed = command.is_user_failed_in_course(mocker.ANY, mocker.ANY)

    assert is_user_failed is expected_result


@pytest.mark.django_db
def test_command_update_is_prerequisite_courses_passed_with_no_prerequisites():
    """
    Test to check if management command issues a system exits upon no prerequisites
    """
    with pytest.raises(SystemExit) as wrapped_exception:
        call_command('update_is_prerequisite_courses_passed')

    assert wrapped_exception.type == SystemExit


@pytest.mark.django_db
@pytest.mark.parametrize('create_users', [1], indirect=True)
@pytest.mark.parametrize('create_courses', [[True]], indirect=True)
@pytest.mark.parametrize('enroll_users', [[False]], indirect=True)
def test_command_update_is_prerequisite_courses_passed_with_no_minimal_user(enroll_users):
    """
    Test to check if management command does not update `is_prerequisite_courses_passed` flag if minimal users are zero
    """
    _, user = enroll_users

    call_command('update_is_prerequisite_courses_passed')

    user_application_hub = ApplicationHubFactory(user=user)

    assert user_application_hub.is_prerequisite_courses_passed is False


@pytest.mark.django_db
@pytest.mark.parametrize('create_users', [1], indirect=True)
@pytest.mark.parametrize('create_courses', [[True]], indirect=True)
@pytest.mark.parametrize('enroll_users', [[True]], indirect=True)
@pytest.mark.parametrize('is_user_failed_in_course, expected_result', [(True, False), (False, True)],
                         ids=['passed', 'failed'])
def test_command_update_is_prerequisite_courses_passed_for_passed_and_failed_user(
        mocker, enroll_users, is_user_failed_in_course, expected_result):
    """
    Test to check if management command does not update `is_prerequisite_courses_passed` flag if user has not passed the
    course but updates `is_prerequisite_courses_passed` flag if user has passed the course
    """
    _, user = enroll_users

    mocker.patch.object(command_module.Command, 'is_user_failed_in_course', return_value=is_user_failed_in_course)
    mocker.patch.object(command_module.Command, 'get_minimal_users_to_be_checked_for_update',
                        return_value=[user])

    call_command('update_is_prerequisite_courses_passed')

    user_application_hub = ApplicationHubFactory(user=user)

    assert user_application_hub.is_prerequisite_courses_passed is expected_result
