"""
All tests for applications views
"""
import os
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from dateutil.relativedelta import relativedelta
from django.core.files import File

from openedx.adg.lms.applications.constants import RESUME_FILE_MAX_SIZE
from openedx.adg.lms.applications.forms import (
    ExtendedUserProfileForm,
    UserApplicationCoverLetterForm,
    UserApplicationForm
)
from openedx.adg.lms.registration_extension.tests.factories import ExtendedUserProfileFactory

from .constants import MOCK_FILE_PATH
from .factories import BusinessLineFactory


@pytest.fixture(name='user_extended_profile')
def user_extended_profile_fixture():
    """
    Create user and related profile factories
    """
    return ExtendedUserProfileFactory()


def birth_date_dictionary(birth_date):
    """
    Initialize the data dictionary for birth_date of extended profile form
    """
    return {
        'birth_day': birth_date.day,
        'birth_month': birth_date.month,
        'birth_year': birth_date.year
    }


def test_extended_user_profile_form_with_future_birth_date():
    """
    Validate that future dates are not allowed in birth_date field
    """
    tomorrow = date.today() + timedelta(days=1)
    form = ExtendedUserProfileForm(data=birth_date_dictionary(tomorrow))
    assert not form.is_valid()


def test_extended_user_profile_form_with_invalid_date():
    """
    Validate that future dates are not allowed in birth_date field
    """
    data = {
        'birth_day': 30,
        'birth_month': 2,
        'birth_year': 2000
    }
    form = ExtendedUserProfileForm(data=data)
    assert not form.is_valid()


@pytest.mark.parametrize('age_year , expected', [(21, True), (61, False)])
def test_extended_user_profile_form_with_birth_date(age_year, expected):
    """
    Validate that birth_date with at least 21 year difference is allowed
    """
    age = date.today() - relativedelta(years=age_year)
    form = ExtendedUserProfileForm(data=birth_date_dictionary(age))
    assert form.is_valid() == expected


@pytest.mark.django_db
def test_extended_user_profile_form_valid_data(user_extended_profile):
    """
    Validate that valid data is stored in database successfully
    """
    user = user_extended_profile.user
    birth_date = date.today() - relativedelta(years=30)
    form = ExtendedUserProfileForm(data=birth_date_dictionary(birth_date))
    mocked_request = MagicMock()
    mocked_request.user = user
    if form.is_valid():
        form.save(request=mocked_request)
    user_extended_profile.refresh_from_db()
    assert birth_date == user_extended_profile.birth_date


@pytest.mark.parametrize('size , expected', [(RESUME_FILE_MAX_SIZE, True), (RESUME_FILE_MAX_SIZE + 1, False)])
def test_user_application_form_with_resume_size(size, expected):
    """
    Validate resume size is less than maximum allowed size
    """
    path = 'dummy_file.pdf'
    with open(path, 'w') as f:
        mocked_file = File(f)
    mocked_file.size = size
    file_dict = {'resume': mocked_file}
    form = UserApplicationForm(None, files=file_dict)
    assert form.is_valid() == expected
    os.remove(path)


# ------- Application Cover Letter Form tests below -------


@pytest.fixture(name='mock_cover_letter_file')
def mock_cover_letter_file_fixture():
    """
    Creates a mock cover letter file
    Returns:
        File object
    """
    with open(MOCK_FILE_PATH, 'w') as f:
        mocked_file = File(f)

    yield mocked_file

    os.remove(MOCK_FILE_PATH)


@pytest.mark.django_db
@pytest.mark.parametrize('expected', [True, False], ids=['business_line_selected', 'no_business_line'])
def test_user_application_cover_letter_form_business_line(expected):
    """
    Validate that business line is a compulsory field
    """
    if expected:
        business_line = BusinessLineFactory().id
    else:
        business_line = None

    data_dict = {'business_line': business_line}
    form = UserApplicationCoverLetterForm(data=data_dict)

    assert form.is_valid() == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    'data, expected',
    [
        ('cover_letter', True),
        ('cover_letter_file', True),
        ('cover_letter and cover_letter_file', False)
    ],
    ids=['cover_letter', 'cover_letter_file', 'cover_letter_and_cover_letter_file'])
def test_user_application_cover_letter_form_cover_letter_and_cover_letter_file(data, expected, mock_cover_letter_file):
    """
    Validate that either cover letter or cover letter file is being sent; not both
    """
    business_line = BusinessLineFactory().id
    data_dict = {'business_line': business_line}
    file_dict = None

    if data != 'cover_letter_file':
        data_dict['cover_letter'] = 'cover_letter_text'

    if data != 'cover_letter':
        mock_cover_letter_file.size = RESUME_FILE_MAX_SIZE

        file_dict = {'cover_letter_file': mock_cover_letter_file}

    form = UserApplicationCoverLetterForm(data=data_dict, files=file_dict)

    assert form.is_valid() == expected


@pytest.mark.django_db
@pytest.mark.parametrize('size , expected', [(RESUME_FILE_MAX_SIZE, True), (RESUME_FILE_MAX_SIZE + 1, False)])
def test_user_application_cover_letter_form_file_size(size, expected, mock_cover_letter_file):
    """
    Validate cover letter file size is less than maximum allowed size
    """
    business_line = BusinessLineFactory().id

    mock_cover_letter_file.size = size

    file_dict = {'cover_letter_file': mock_cover_letter_file}
    data_dict = {'business_line': business_line}
    form = UserApplicationCoverLetterForm(data=data_dict, files=file_dict)

    assert form.is_valid() == expected
