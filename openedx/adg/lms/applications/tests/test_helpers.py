"""
All tests for applications helpers functions
"""
import logging
from datetime import date
from unittest.mock import Mock, patch

import mock
import pytest
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.grades.models import PersistentCourseGrade
from openedx.adg.lms.applications import helpers
from openedx.adg.lms.applications.constants import (
    APPLICATION_SUBMISSION_CONGRATS,
    APPLICATION_SUBMISSION_INSTRUCTION,
    BACKGROUND_QUESTION_TITLE,
    BU_PREREQ_COURSES_TITLE,
    COMPLETED,
    FILE_MAX_SIZE,
    IN_PROGRESS,
    LOCKED,
    LOCKED_COURSE_MESSAGE,
    LOGO_IMAGE_MAX_SIZE,
    MAX_NUMBER_OF_WORDS_ALLOWED_IN_TEXT_INPUT,
    MAXIMUM_YEAR_OPTION,
    MINIMUM_YEAR_OPTION,
    MONTH_NAME_DAY_YEAR_FORMAT,
    NOT_STARTED,
    PREREQUISITE_COURSES_COMPLETION_CONGRATS,
    PREREQUISITE_COURSES_COMPLETION_INSTRUCTION,
    PREREQUISITE_COURSES_COMPLETION_MSG,
    PROGRAM_PREREQ_COURSES_TITLE,
    RETAKE,
    RETAKE_COURSE_MESSAGE,
    SCORES,
    WRITTEN_APPLICATION_COMPLETION_CONGRATS,
    WRITTEN_APPLICATION_COMPLETION_INSTRUCTION,
    WRITTEN_APPLICATION_COMPLETION_MSG,
    CourseScore
)
from openedx.adg.lms.applications.helpers import (
    _get_application_review_info,
    bulk_update_application_hub_flag,
    check_validations_for_current_record,
    check_validations_for_past_record,
    create_html_string_for_course_scores_in_admin_review,
    get_application_hub_instructions,
    get_course_card_information,
    get_courses_from_course_groups,
    get_duration,
    get_extra_context_for_application_review_page,
    get_user_scores_for_courses,
    get_users_with_active_enrollments_from_course_groups,
    has_admin_permissions,
    has_user_passed_given_courses,
    is_user_qualified_for_bu_prereq_courses,
    max_year_value_validator,
    min_year_value_validator,
    send_application_submission_confirmation_emails,
    validate_file_size,
    validate_logo_size,
    validate_word_limit
)
from openedx.adg.lms.applications.models import UserApplication
from openedx.adg.lms.applications.tests.factories import (
    ApplicationHubFactory,
    CourseOverviewFactory,
    MultilingualCourseFactory,
    MultilingualCourseGroupFactory,
    UserApplicationFactory
)
from openedx.core.lib.grade_utils import round_away_from_zero

from .constants import EMAILS, PROGRAM_PRE_REQ, TEST_TEXT_INPUT
from .factories import ApplicationHubFactory

DATE_COMPLETED_MONTH = 5
DATE_COMPLETED_YEAR = 2020
DATE_STARTED_MONTH = 2
DATE_STARTED_YEAR = 2018
ERROR_MESSAGE = '{key}, some error message'


def test_validate_logo_size_with_valid_size():
    """
    Verify that file size up to LOGO_IMAGE_MAX_SIZE is allowed
    """
    mocked_file = Mock()
    mocked_file.size = LOGO_IMAGE_MAX_SIZE
    validate_logo_size(mocked_file)


def test_validate_logo_size_with_invalid_size():
    """
    Verify that size greater than LOGO_IMAGE_MAX_SIZE is not allowed
    """
    mocked_file = Mock()
    mocked_file.size = LOGO_IMAGE_MAX_SIZE + 1
    with pytest.raises(Exception):
        validate_logo_size(mocked_file)


@patch('openedx.adg.lms.applications.helpers.task_send_mandrill_email')
def test_send_application_submission_confirmation_emails(mocked_task_send_mandrill_email):
    """
    Check if the emails are being sent correctly
    """
    send_application_submission_confirmation_emails(EMAILS)
    assert mocked_task_send_mandrill_email.delay.called


def test_min_year_value_validator_invalid():
    """
    Check if invalid value for min year value validator raises error
    """
    with pytest.raises(ValidationError):
        min_year_value_validator(MINIMUM_YEAR_OPTION - 1)


def test_min_year_value_validator_valid():
    """
    Check if invalid value for min year value validator raises error
    """
    assert min_year_value_validator(MINIMUM_YEAR_OPTION) is None


def test_max_year_value_validator_invalid():
    """
    Check if invalid value for max year value validator raises error
    """
    with pytest.raises(ValidationError):
        max_year_value_validator(MAXIMUM_YEAR_OPTION + 1)


def test_max_year_value_validator_valid():
    """
    Check if invalid value for max year value validator raises error
    """
    assert max_year_value_validator(MAXIMUM_YEAR_OPTION) is None


@pytest.mark.parametrize('date_attrs_with_expected_results', [
    {
        'attrs': {
            'date_started_month': 1,
            'date_started_year': date.today().year - 1,
        },
        'expected_result': {}
    },
    {
        'attrs': {
            'date_started_month': 1,
            'date_started_year': date.today().year - 1,
            'date_completed_month': DATE_COMPLETED_MONTH
        },
        'expected_result': {
            'date_completed_month': ERROR_MESSAGE.format(key='Date completed month')
        }
    },
    {
        'attrs': {
            'date_started_month': 1,
            'date_started_year': date.today().year - 1,
            'date_completed_year': DATE_COMPLETED_YEAR
        },
        'expected_result': {
            'date_completed_year': ERROR_MESSAGE.format(key='Date completed year')
        }
    },
    {
        'attrs': {
            'date_started_month': 1,
            'date_started_year': date.today().year + 1,
            'date_completed_month': DATE_COMPLETED_MONTH,
            'date_completed_year': DATE_COMPLETED_YEAR,
        },
        'expected_result': {
            'date_completed_month': ERROR_MESSAGE.format(key='Date completed month'),
            'date_completed_year': ERROR_MESSAGE.format(key='Date completed year'),
            'date_started_year': 'Date should not be in future',
        }
    },
])
def test_check_validations_for_current_record(date_attrs_with_expected_results):
    """
    Check for expected validation errors against provided data
    """
    actual_result = check_validations_for_current_record(date_attrs_with_expected_results['attrs'], ERROR_MESSAGE)
    assert actual_result == date_attrs_with_expected_results['expected_result']


@pytest.mark.parametrize('date_attrs_with_expected_results', [
    {
        'attrs': {'date_started_month': DATE_COMPLETED_MONTH, 'date_started_year': DATE_COMPLETED_YEAR},
        'expected_result': {
            'date_completed_month': ERROR_MESSAGE.format(key='Date completed month'),
            'date_completed_year': ERROR_MESSAGE.format(key='Date completed year')
        }
    },
    {
        'attrs': {
            'date_completed_month': DATE_COMPLETED_MONTH,
            'date_started_month': DATE_STARTED_MONTH,
            'date_started_year': DATE_STARTED_YEAR
        },
        'expected_result': {'date_completed_year': ERROR_MESSAGE.format(key='Date completed year')}
    },
    {
        'attrs': {
            'date_completed_year': DATE_COMPLETED_YEAR,
            'date_started_month': DATE_STARTED_MONTH,
            'date_started_year': DATE_STARTED_YEAR
        },
        'expected_result': {'date_completed_month': ERROR_MESSAGE.format(key='Date completed month')}
    },
    {
        'attrs': {
            'date_completed_month': DATE_COMPLETED_MONTH,
            'date_completed_year': DATE_COMPLETED_YEAR,
            'date_started_month': DATE_STARTED_MONTH,
            'date_started_year': DATE_STARTED_YEAR
        },
        'expected_result': {}
    },
    {
        'attrs': {
            'date_completed_month': DATE_COMPLETED_MONTH,
            'date_completed_year': DATE_COMPLETED_YEAR,
            'date_started_month': DATE_STARTED_MONTH,
            'date_started_year': DATE_COMPLETED_YEAR + 1
        },
        'expected_result': {'date_completed_year': 'Completed date must be greater than started date.'}
    }
])
def test_check_validations_for_past_record(date_attrs_with_expected_results):
    """
    Check for expected validation errors against provided data
    """
    actual_result = check_validations_for_past_record(date_attrs_with_expected_results['attrs'], ERROR_MESSAGE)
    assert actual_result == date_attrs_with_expected_results['expected_result']


@pytest.mark.parametrize('size , expected', [
    (FILE_MAX_SIZE, None),
    (FILE_MAX_SIZE + 1, 'File size must not exceed 4.0 MB')
])
def test_validate_file_size_with_valid_size(size, expected):
    """
    Verify that file size up to max_size i.e. FILE_MAX_SIZE is allowed
    """
    mocked_file = Mock()
    mocked_file.size = size
    error = validate_file_size(mocked_file, FILE_MAX_SIZE)
    assert error == expected


@pytest.mark.parametrize(
    'is_current, expected_duration', [
        (True, 'January 2020 to Present'),
        (False, 'January 2020 to December 2020')
    ]
)
@pytest.mark.django_db
def test_get_duration(is_current, expected_duration, work_experience):
    """
    Test that the `get_duration` function returns the time duration in the correct format when provided with a
    `UserStartAndEndDates` entry.
    """
    work_experience.date_started_month = 1
    work_experience.date_started_year = 2020

    if not is_current:
        work_experience.date_completed_month = 12
        work_experience.date_completed_year = 2020

    actual_duration = get_duration(work_experience, is_current)

    assert expected_duration == actual_duration


@pytest.mark.parametrize(
    'application_status', [UserApplication.OPEN, UserApplication.WAITLIST]
)
@pytest.mark.django_db
def test_get_application_review_info(user_application, application_status):
    """
    Test that the `_get_application_review_info` function extracts and returns the correct reviewer and review date from
    the input application, depending upon the application status.
    """
    user_application.status = application_status

    if application_status == UserApplication.OPEN:
        expected_reviewed_by = None
        expected_review_date = None
    else:
        reviewer = UserFactory()
        user_application.reviewed_by = reviewer

        current_date = date.today()
        user_application.modified = current_date

        expected_reviewed_by = reviewer.profile.name
        expected_review_date = current_date.strftime(MONTH_NAME_DAY_YEAR_FORMAT)

    expected_review_info = expected_reviewed_by, expected_review_date
    actual_review_info = _get_application_review_info(user_application)

    assert expected_review_info == actual_review_info


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.helpers._get_application_review_info')
def test_get_extra_context_for_application_review_page(mock_get_application_review_info, user_application):
    """
    Test that the `get_extra_context_for_application_review_page` function returns the correct context when provided
    with an application.
    """
    mock_get_application_review_info.return_value = 'reviewed_by', 'review_date'

    expected_context = {
        'title': user_application.user.profile.name,
        'adg_view': True,
        'application': user_application,
        'reviewer': 'reviewed_by',
        'review_date': 'review_date',
        'SCORES': SCORES,
        'BACKGROUND_QUESTION': BACKGROUND_QUESTION_TITLE,
    }
    actual_context = get_extra_context_for_application_review_page(user_application)

    assert expected_context == actual_context


@pytest.mark.django_db
@pytest.mark.parametrize(
    'is_staff, is_superuser, is_business_line_admin, expected_result',
    [
        (False, False, False, False),
        (False, False, True, False),
        (False, True, False, False),
        (False, True, True, False),
        (True, False, False, False),
        (True, False, True, True),
        (True, True, False, True),
        (True, True, True, True),
    ]
)
def test_has_admin_permissions(mocker, is_business_line_admin, is_superuser, is_staff, expected_result):
    """
    Test if the user is a superuser or an ADG admin or the admin of any Business line while having the staff
    status
    """
    mocked_class = mocker.patch('openedx.adg.lms.applications.models.BusinessLine')
    mocked_class.is_user_business_line_admin.return_value = is_business_line_admin

    test_user = UserFactory(is_superuser=is_superuser, is_staff=is_staff)

    assert has_admin_permissions(test_user) == expected_result


@pytest.mark.django_db
def test_get_courses_from_course_groups(user_client, courses):
    """
    Tests `get_courses_from_course_groups` returns a valid list of courses.
    """
    user, _ = user_client

    UserApplicationFactory(user=user)
    ApplicationHubFactory(user=user)

    course_group = MultilingualCourseGroupFactory(is_common_business_line_prerequisite=True)
    MultilingualCourseFactory(
        course=courses['test_course1'],
        multilingual_course_group=course_group
    )

    catalog_courses = get_courses_from_course_groups([course_group], user)

    assert catalog_courses == [courses['test_course1']]


@pytest.mark.django_db
def test_user_is_not_qualified_for_bu_prereq_courses(user_client):
    """
    Tests `is_user_qualified_for_bu_prereq_courses` returns `False` for a user with no application and application_hub.
    """
    user, _ = user_client
    assert not is_user_qualified_for_bu_prereq_courses(user)


@pytest.mark.django_db
def test_user_is_qualified_for_bu_prereq_courses(user_client):
    """
    Tests `is_user_qualified_for_bu_prereq_courses` returns `True` for user with application and application_hub and
    has passed program prerequisites.
    """
    user, _ = user_client
    UserApplicationFactory(user=user)
    ApplicationHubFactory(user=user, is_prerequisite_courses_passed=True)
    assert is_user_qualified_for_bu_prereq_courses(user)


@pytest.mark.parametrize('text_input, is_valid', [
    (TEST_TEXT_INPUT, True),
    (TEST_TEXT_INPUT * MAX_NUMBER_OF_WORDS_ALLOWED_IN_TEXT_INPUT, True),
    (TEST_TEXT_INPUT * (MAX_NUMBER_OF_WORDS_ALLOWED_IN_TEXT_INPUT + 1), False)
])
@pytest.mark.django_db
def test_validate_word_limit(text_input, is_valid):
    """
    Check if the `validate_word_limit` function raises a ValidationError if the total
    number of words exceed the provided limit
    """
    if is_valid:
        assert not validate_word_limit(text_input)
    else:
        with pytest.raises(ValidationError):
            validate_word_limit(text_input)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'written_application, omni_courses, bu_courses, omni_courses_started, bu_courses_started, congrats, msg, inst',
    [
        (False, False, False, False, False, '', '', ''),
        (
            True, False, False, False, False, WRITTEN_APPLICATION_COMPLETION_CONGRATS,
            WRITTEN_APPLICATION_COMPLETION_MSG, ''
        ),
        (True, False, False, True, False, '', '', WRITTEN_APPLICATION_COMPLETION_INSTRUCTION),
        (
            True, True, False, False, False, PREREQUISITE_COURSES_COMPLETION_CONGRATS,
            PREREQUISITE_COURSES_COMPLETION_MSG, ''
        ),
        (True, True, False, False, True, '', '', PREREQUISITE_COURSES_COMPLETION_INSTRUCTION),
        (True, True, True, False, False, APPLICATION_SUBMISSION_CONGRATS, APPLICATION_SUBMISSION_INSTRUCTION, ''),
    ],
    ids=[
        'no_step_completed', 'written_app_completed', 'omni_courses_started',
        'omni_courses_completed', 'bu_courses_started', 'all_steps_completed'
    ]
)
def test_get_application_hub_instructions(
    written_application,
    omni_courses,
    bu_courses,
    omni_courses_started,
    bu_courses_started,
    congrats,
    msg,
    inst,
    test_user
):
    """
    Test the congratulation messages and instructions for each requirement completion till application submission.
    """
    application_hub = ApplicationHubFactory(user=test_user)

    if written_application:
        application_hub.submit_written_application_for_current_date()
    if omni_courses:
        application_hub.set_is_prerequisite_courses_passed()
    if bu_courses:
        application_hub.set_is_bu_prerequisite_courses_passed()

    actual_messages = get_application_hub_instructions(application_hub, omni_courses_started, bu_courses_started)

    expected_messages = {
        'congrats': congrats,
        'message': msg,
        'instruction': inst
    }

    assert actual_messages == expected_messages


@pytest.mark.django_db
@pytest.mark.parametrize(
    'is_enrolled, is_completed, all_modules_attempted, status, grade, message',
    [
        (False, False, False, NOT_STARTED, '', ''),
        (True, False, False, IN_PROGRESS, '', ''),
        (True, False, True, RETAKE, '0', RETAKE_COURSE_MESSAGE),
        (True, True, True, COMPLETED, '100', ''),
    ],
    ids=['not_enrolled', 'enrolled_in_course', 'failed_in_course', 'completed_course']
)
def test_get_course_card_information_with_and_without_enrollment(
    is_enrolled, is_completed, all_modules_attempted, status, grade, message, test_user, mocker
):
    """
    Test the course card information when the user has not enrolled in a course, when the user has enrolled in a course,
    when the user has failed the course and when the user has completed the course
    """
    if is_completed:
        mocker.patch.object(helpers.CourseGradeFactory, 'read', return_value=Mock(passed=True, percent=1))
    elif is_enrolled:
        mocker.patch(
            'openedx.adg.lms.applications.helpers.has_attempted_all_modules', return_value=all_modules_attempted
        )

    course = CourseOverviewFactory()

    if is_enrolled:
        CourseEnrollmentFactory(user=test_user, course=course)

    course_cards, is_any_course_started, is_locked = get_course_card_information(test_user, [course])

    assert course_cards == [{
        'course': course,
        'status': status,
        'grade': grade,
        'message': message
    }]

    assert is_any_course_started if is_enrolled else not is_any_course_started
    assert not is_locked


@pytest.mark.django_db
@pytest.mark.parametrize(
    'is_passed, status, message, is_course_locked',
    [
        (False, LOCKED, LOCKED_COURSE_MESSAGE, True),
        (True, NOT_STARTED, '', False),
    ],
    ids=['un_passed_prerequisite', 'passed_prerequisite']
)
def test_get_course_card_information_of_a_course_with_prerequisite(
    is_passed, status, message, is_course_locked, test_user, mocker
):
    """
    Test the course card information when a course has a prerequisite that has not been passed yet and when a course has
    a prerequisite that has been passed
    """
    course = CourseOverviewFactory(display_name='course')
    prerequisite_course = CourseOverviewFactory(display_name='pre_course')

    mocker.patch.object(helpers.CourseGradeFactory, 'read', return_value=Mock(passed=is_passed))
    mocker.patch(
        'openedx.adg.lms.applications.helpers.get_prerequisite_courses_display', return_value=[{
            'key': prerequisite_course.id
        }]
    )

    if is_course_locked:
        message = f'{message} pre_course.'

    course_cards, is_any_course_started, is_locked = get_course_card_information(test_user, [course])

    assert course_cards == [{
        'course': course,
        'status': status,
        'grade': '',
        'message': message
    }]
    assert not is_any_course_started
    assert is_locked == is_course_locked


@pytest.mark.django_db
@pytest.mark.parametrize(
    'percent_grades, letter_grades, passed, expected_result',
    [
        ([80, 80], ['A', 'A'], [True, True], True),
        ([80, 0], ['A', ''], [True, False], False),
    ]
)
def test_has_user_passed_given_courses(courses, percent_grades, letter_grades, passed, expected_result):
    """
    Assert that for a given course group of courses True is returned only if user has passed all courses
    """
    user = UserFactory()
    for itr, course in enumerate(courses.values()):
        PersistentCourseGrade.update_or_create(
            user_id=user.id,
            course_id=course.id,
            percent_grade=percent_grades[itr],
            letter_grade=letter_grades[itr],
            passed=passed,
        )

    assert has_user_passed_given_courses(user, courses.values()) == expected_result


@pytest.mark.django_db
@pytest.mark.parametrize('prereq_course_groups', [(1, PROGRAM_PRE_REQ)], indirect=True)
def test_get_users_with_active_enrollments_from_course_groups(prereq_course_groups):
    """
    Assert that only users that are enrolled in multilingual courses are returned.
    """
    users = UserFactory.create_batch(5)
    users_ids = [user.id for user in users]

    open_multilingual_courses = prereq_course_groups[0].multilingual_courses.open_multilingual_courses()
    CourseEnrollmentFactory(user=users[0], course=open_multilingual_courses[0].course)

    assert get_users_with_active_enrollments_from_course_groups(users_ids, prereq_course_groups) == [users[0]]


@pytest.mark.django_db
@pytest.mark.parametrize('flag', ('is_prerequisite_courses_passed', 'is_bu_prerequisite_courses_passed'))
def test_bulk_update_application_hub_flag(flag, caplog):
    """
    Assert that flag is successfully updated in application hub model
    """
    application_hubs = ApplicationHubFactory.create_batch(2)
    users = [application_hub.user for application_hub in application_hubs]

    caplog.set_level(logging.INFO)
    bulk_update_application_hub_flag(flag, users)

    for application_hub in application_hubs:
        application_hub.refresh_from_db()
        if flag == 'is_prerequisite_courses_passed':
            assert application_hub.is_prerequisite_courses_passed
        else:
            assert application_hub.is_bu_prerequisite_courses_passed

    assert f'`{flag}` flag is updated' in caplog.messages[0]


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.helpers.CourseGradeFactory.read')
def test_get_user_scores_for_courses(mock_read, courses):
    """
    Tests that the `get_user_scores_for_courses` returns the course scores for the given
    courses
    """
    user = UserFactory()
    test_course_1 = courses['test_course1']
    test_course_2 = courses['test_course2']
    percent = 0.78

    course_grade = CourseGradeFactory()
    course_grade.percent = percent
    mock_read.return_value = course_grade

    score = int(round_away_from_zero(course_grade.percent * 100))
    course_score_1 = CourseScore(test_course_1.display_name, score)
    course_score_2 = CourseScore(test_course_2.display_name, score)

    expected_scores = [course_score_1, course_score_2]
    actual_scores = get_user_scores_for_courses(user, [test_course_1, test_course_2])

    assert actual_scores == expected_scores


@pytest.mark.django_db
@pytest.mark.parametrize(
    'program_prereq_scores, bu_prereq_scores',
    [
        (False, False),
        (True, False),
        (False, True),
        (True, True)
    ]
)
def test_create_html_string_for_course_scores_in_admin_review(program_prereq_scores, bu_prereq_scores, courses):
    """
    Tests that a correct html string is genereated containing the right course scores and
    their names along with the section heading
    """
    user_application = Mock()
    test_course_1 = courses['test_course1']
    test_course_2 = courses['test_course2']
    percentage = 0.78
    course_percentage = int(round_away_from_zero(percentage * 100))
    html_for_score = '<p>{course_name}: <b>{score}%</b></p>'

    expected_html = ''
    if program_prereq_scores:
        user_application.program_prereq_course_scores = [CourseScore(test_course_1.display_name, course_percentage)]
        expected_html += f'<br>{PROGRAM_PREREQ_COURSES_TITLE}'
        expected_html += html_for_score.format(course_name=test_course_1.display_name, score=course_percentage)
    else:
        user_application.program_prereq_course_scores = []

    if bu_prereq_scores:
        user_application.bu_prereq_course_scores = [CourseScore(test_course_2.display_name, course_percentage)]
        expected_html += f'<br>{BU_PREREQ_COURSES_TITLE}'
        expected_html += html_for_score.format(course_name=test_course_2.display_name, score=course_percentage)
    else:
        user_application.bu_prereq_course_scores = []

    expected_result = format_html(expected_html)
    actual_result = create_html_string_for_course_scores_in_admin_review(user_application)
    assert expected_result == actual_result
