"""
All tests for applications helpers functions
"""
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

import mock
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.html import format_html

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from openedx.adg.lms.applications.constants import (
    COVER_LETTER_ONLY,
    FILE_MAX_SIZE,
    HTML_FOR_EMBEDDED_FILE_VIEW,
    LOGO_IMAGE_MAX_SIZE,
    MAXIMUM_YEAR_OPTION,
    MINIMUM_YEAR_OPTION,
    MONTH_NAME_DAY_YEAR_FORMAT,
    SCORES
)
from openedx.adg.lms.applications.helpers import (
    _get_application_review_info,
    check_validations_for_current_record,
    check_validations_for_past_record,
    get_duration,
    get_embedded_view_html,
    get_extra_context_for_application_review_page,
    get_prerequisite_courses_for_user,
    is_displayable_on_browser,
    max_year_value_validator,
    min_year_value_validator,
    send_application_submission_confirmation_email,
    validate_file_size,
    validate_logo_size
)
from openedx.adg.lms.applications.models import UserApplication
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory

from .constants import EMAIL
from .factories import MultilingualCourseFactory, MultilingualCourseGroupFactory

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


@patch('openedx.adg.lms.applications.helpers.MandrillClient')
def test_send_application_submission_confirmation_email(mocked_mandrill_client):
    """
    Check if the email is being sent correctly
    """
    send_application_submission_confirmation_email(EMAIL)
    assert mocked_mandrill_client().send_mandrill_email.called


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
        'expected_result': {'date_completed_year': 'Completion date must comes after started date'}
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
@mock.patch('openedx.adg.lms.applications.helpers.modulestore')
def test_get_prerequisites_for_user(mock_module_store):
    """
    Test to get prerequisites for user
    """
    mock_module_store.get_course.return_value = mock.Mock()
    MultilingualCourseFactory()
    user = UserFactory()
    assert len(get_prerequisite_courses_for_user(user)) == 1


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.helpers.modulestore')
def test_no_prerequisite_courses(mock_module_store):
    """
    Test no prerequisites courses for user
    """
    mock_module_store.get_course.return_value = mock.Mock()
    MultilingualCourseGroupFactory()
    user = UserFactory()
    assert len(get_prerequisite_courses_for_user(user)) == 0


@pytest.mark.django_db
def test_get_enrolled_prerequisites_for_user():
    """
    Test to get enrolled prerequisites for user
    """
    user = UserFactory()
    current_time = datetime.now()
    course = CourseOverviewFactory(
        start_date=current_time - timedelta(days=1),
        end_date=current_time + timedelta(days=1)
    )
    MultilingualCourseFactory(course=course)
    CourseEnrollmentFactory(course=course, user=user, is_active=True)
    assert len(get_prerequisite_courses_for_user(user)) == 1
