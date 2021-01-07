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
from openedx.adg.lms.applications.forms import ExtendedUserProfileForm, UserApplicationForm
from openedx.adg.lms.registration_extension.tests.factories import ExtendedUserProfileFactory


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
