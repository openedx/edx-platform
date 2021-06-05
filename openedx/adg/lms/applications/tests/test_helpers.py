"""
All tests for applications helpers functions
"""
from datetime import date
from unittest.mock import Mock, patch

import mock
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.html import format_html

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from openedx.adg.lms.applications import helpers
from openedx.adg.lms.applications.constants import (
    APPLICATION_SUBMISSION_CONGRATS,
    APPLICATION_SUBMISSION_INSTRUCTION,
    COMPLETED,
    COVER_LETTER_ONLY,
    FILE_MAX_SIZE,
    HTML_FOR_EMBEDDED_FILE_VIEW,
    IN_PROGRESS,
    LOCKED,
    LOCKED_COURSE_MESSAGE,
    LOGO_IMAGE_MAX_SIZE,
    MAXIMUM_YEAR_OPTION,
    MINIMUM_YEAR_OPTION,
    MONTH_NAME_DAY_YEAR_FORMAT,
    NOT_STARTED,
    PREREQUISITE_COURSES_COMPLETION_CONGRATS,
    PREREQUISITE_COURSES_COMPLETION_INSTRUCTION,
    PREREQUISITE_COURSES_COMPLETION_MSG,
    RETAKE,
    RETAKE_COURSE_MESSAGE,
    SCORES,
    WRITTEN_APPLICATION_COMPLETION_CONGRATS,
    WRITTEN_APPLICATION_COMPLETION_INSTRUCTION,
    WRITTEN_APPLICATION_COMPLETION_MSG
)
from openedx.adg.lms.applications.helpers import (
    _get_application_review_info,
    check_validations_for_current_record,
    check_validations_for_past_record,
    get_application_hub_instructions,
    get_course_card_information,
    get_courses_from_course_groups,
    get_duration,
    get_embedded_view_html,
    get_extra_context_for_application_review_page,
    has_admin_permissions,
    is_displayable_on_browser,
    max_year_value_validator,
    min_year_value_validator,
    send_application_submission_confirmation_email,
    validate_file_size,
    validate_logo_size
)
from openedx.adg.lms.applications.models import UserApplication
from openedx.adg.lms.applications.tests.factories import (
    ApplicationHubFactory,
    CourseOverviewFactory,
    MultilingualCourseFactory,
    MultilingualCourseGroupFactory,
    UserApplicationFactory
)

from .constants import EMAIL
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
def test_send_application_submission_confirmation_email(mocked_task_send_mandrill_email):
    """
    Check if the email is being sent correctly
    """
    send_application_submission_confirmation_email(EMAIL)
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
    'filename, expected_is_displayable_on_browser', [
        ('test.pdf', True),
        ('test.doc', False)
    ]
)
def test_is_displayable_on_browser(filename, expected_is_displayable_on_browser):
    """
    Test that the `is_displayable_on_browser` function returns False if the input file is a .doc file, True otherwise.
    """
    test_file = SimpleUploadedFile(filename, b'')
    actual_is_displayable_on_browser = is_displayable_on_browser(test_file)

    assert expected_is_displayable_on_browser == actual_is_displayable_on_browser


def test_get_embedded_view_html():
    """
    Test that the `get_embedded_view_html` function returns the correct and safe HTML to render the input file in an
    embedded view.
    """
    test_file = SimpleUploadedFile('test.pdf', b'')
    test_file.url = 'test_url'

    expected_html = format_html(HTML_FOR_EMBEDDED_FILE_VIEW.format(path_to_file=test_file.url))
    actual_html = get_embedded_view_html(test_file)

    assert expected_html == actual_html


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
        'COVER_LETTER_ONLY': COVER_LETTER_ONLY,
        'SCORES': SCORES
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
def test_get_course_card_information_after_enrolling_and_failing_course(
    is_enrolled, is_completed, all_modules_attempted, status, grade, message, test_user, mocker
):
    """
    Test the course card information when the user has enrolled in a course and when the user has failed the course
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
