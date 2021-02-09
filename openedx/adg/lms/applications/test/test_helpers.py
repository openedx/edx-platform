"""
All tests for applications helpers functions
"""
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError

from openedx.adg.lms.applications.constants import (
    LOGO_IMAGE_MAX_SIZE,
    MAXIMUM_YEAR_OPTION,
    MINIMUM_YEAR_OPTION,
    FILE_MAX_SIZE
)
from openedx.adg.lms.applications.helpers import (
    check_validations_for_current_record,
    check_validations_for_past_record,
    max_year_value_validator,
    min_year_value_validator,
    send_application_submission_confirmation_email,
    validate_file_size,
    validate_logo_size
)

from .constants import EMAIL

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


@patch('openedx.adg.lms.applications.helpers.send_mandrill_email')
def test_send_application_submission_confirmation_email(mock_mandrill_email):
    """
    Check if the email is being sent correctly
    """
    send_application_submission_confirmation_email(EMAIL)
    assert mock_mandrill_email.called


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
        'attrs': {},
        'expected_result': {}
    },
    {
        'attrs': {'date_completed_month': DATE_COMPLETED_MONTH},
        'expected_result': {'date_completed_month': ERROR_MESSAGE.format(key='Date completed month')}
    },
    {
        'attrs': {'date_completed_year': DATE_COMPLETED_YEAR},
        'expected_result': {'date_completed_year': ERROR_MESSAGE.format(key='Date completed year')}
    },
    {
        'attrs': {'date_completed_month': DATE_COMPLETED_MONTH, 'date_completed_year': DATE_COMPLETED_YEAR},
        'expected_result': {
            'date_completed_month': ERROR_MESSAGE.format(key='Date completed month'),
            'date_completed_year': ERROR_MESSAGE.format(key='Date completed year')
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
