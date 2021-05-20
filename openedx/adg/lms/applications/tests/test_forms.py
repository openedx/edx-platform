"""
All tests for applications views
"""
import os
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from dateutil.relativedelta import relativedelta
from django.core.files import File

from openedx.adg.lms.applications.admin import UserApplicationADGAdmin
from openedx.adg.lms.applications.constants import (
    APPLICATION_REVIEW_ERROR_MSG,
    COURSE_GROUP_PREREQ_VALIDATION_ERROR,
    FILE_MAX_SIZE
)
from openedx.adg.lms.applications.forms import (
    ExtendedUserProfileForm,
    MultilingualCourseGroupForm,
    UserApplicationCoverLetterForm,
    UserApplicationForm
)
from openedx.adg.lms.registration_extension.tests.factories import ExtendedUserProfileFactory

from .constants import MOCK_FILE_PATH, VALID_USER_BIRTH_DATE_FOR_APPLICATION
from .factories import BusinessLineFactory


@pytest.fixture(name='user_extended_profile')
def user_extended_profile_fixture():
    """
    Create user and related profile factories
    """
    return ExtendedUserProfileFactory()


def get_extended_profile_form_data(birth_date=VALID_USER_BIRTH_DATE_FOR_APPLICATION, saudi_national=True):
    """
    Initialize the data dictionary for the extended profile form

    Arguments:
        birth_date (date): Date for the extended profile form
        saudi_national (Boolean): Saudi national or not

    Returns:
        dict: A dict containing the form data
    """
    return {
        'birth_day': birth_date.day,
        'birth_month': birth_date.month,
        'birth_year': birth_date.year,
        'saudi_national': saudi_national
    }


def test_extended_user_profile_form_with_future_birth_date():
    """
    Validate that future dates are not allowed in birth_date field
    """
    tomorrow = date.today() + timedelta(days=1)
    form = ExtendedUserProfileForm(data=get_extended_profile_form_data(birth_date=tomorrow))
    assert not form.is_valid()


@pytest.mark.parametrize('age_year , expected', [(21, True), (61, False)])
def test_extended_user_profile_form_with_birth_date(age_year, expected):
    """
    Validate that birth_date with at least 21 year difference is allowed
    """
    birth_date = date.today() - relativedelta(years=age_year)
    form = ExtendedUserProfileForm(data=get_extended_profile_form_data(birth_date=birth_date))
    assert form.is_valid() == expected


@pytest.mark.django_db
def test_extended_user_profile_form_valid_data(user_extended_profile):
    """
    Validate that valid data is stored in database successfully
    """
    user = user_extended_profile.user
    form = ExtendedUserProfileForm(data=get_extended_profile_form_data())
    mocked_request = MagicMock()
    mocked_request.user = user
    if form.is_valid():
        form.save(request=mocked_request)
    user_extended_profile.refresh_from_db()
    assert VALID_USER_BIRTH_DATE_FOR_APPLICATION == user_extended_profile.birth_date


@pytest.mark.parametrize('size , expected', [(FILE_MAX_SIZE, True), (FILE_MAX_SIZE + 1, False)])
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


@pytest.mark.parametrize(
    'post_data', [{'internal_note': 'test_note'}, {'status': 'test_status'}],
    ids=['without_status', 'with_status']
)
@pytest.mark.django_db
def test_user_application_admin_form(
    user_application_adg_admin_instance, user_application, request, post_data
):
    """
    Test that `UserApplicationAdminForm` is:
        1. valid when provided with status in post data
        2. not valid and raises correct validation error when not provided with status in post data
    """
    request.POST = post_data

    admin_form_class = UserApplicationADGAdmin.get_form(user_application_adg_admin_instance, request, user_application)
    admin_form = admin_form_class()
    admin_form.is_bound = True

    if 'status' in request.POST:
        assert admin_form.is_valid()
    else:
        assert not admin_form.is_valid()
        assert admin_form.errors['__all__'] == [APPLICATION_REVIEW_ERROR_MSG]


@pytest.mark.django_db
@pytest.mark.parametrize('is_saudi_national, expected_result', [(True, True), (False, False)])
def test_user_application_nationality_validation(is_saudi_national, expected_result):
    """
    Test if the user application validation for saudi_national is working correctly or not
    """
    form = ExtendedUserProfileForm(data=get_extended_profile_form_data(saudi_national=is_saudi_national))
    assert form.is_valid() is expected_result


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
@pytest.mark.parametrize(
    'business_line, button_click, expected',
    [
        (None, 'back', True), ('business', 'back', True), (None, 'submit', False), ('business', 'submit', True)
    ],
    ids=[
        'back_button_clicked with_no_business_line',
        'back_button_clicked_with_business_line_selected',
        'submit_button_clicked_with_no_business_line',
        'submit_button_clicked_with_business_line_selected'
    ]
)
def test_user_application_cover_letter_form_business_line(business_line, button_click, expected):
    """
    Validate that business line is a compulsory field
    """
    if business_line == 'business':
        business_line = BusinessLineFactory().id

    data_dict = {
        'business_line': business_line,
        'button_click': button_click
    }
    form = UserApplicationCoverLetterForm(data=data_dict)

    assert form.is_valid() == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    'cover_letter_text, cover_letter_file, expected',
    [
        ('Test cover letter text', None, True),
        (None, 'Test Cover Letter File', True),
        ('Test cover letter text', 'Test Cover Letter File', False)
    ],
    ids=['cover_letter', 'cover_letter_file', 'cover_letter_and_cover_letter_file'])
def test_user_application_cover_letter_duplication(
    cover_letter_text, cover_letter_file, expected, mock_cover_letter_file
):
    """
    Validate that either cover letter or cover letter file is being sent; not both
    """
    business_line = BusinessLineFactory().id
    data_dict = {'business_line': business_line}
    file_dict = None

    if cover_letter_text:
        data_dict['cover_letter'] = 'cover_letter_text'

    if cover_letter_file:
        mock_cover_letter_file.size = FILE_MAX_SIZE
        file_dict = {'cover_letter_file': mock_cover_letter_file}

    form = UserApplicationCoverLetterForm(data=data_dict, files=file_dict)

    assert form.is_valid() == expected


@pytest.mark.django_db
@pytest.mark.parametrize('size , expected', [(FILE_MAX_SIZE, True), (FILE_MAX_SIZE + 1, False)])
def test_user_application_cover_letter_form_file_size(size, expected, mock_cover_letter_file):
    """
    Validate cover letter file size is less than maximum allowed size
    """
    business_line = BusinessLineFactory().id
    data_dict = {'business_line': business_line}

    mock_cover_letter_file.size = size
    file_dict = {'cover_letter_file': mock_cover_letter_file}

    form = UserApplicationCoverLetterForm(data=data_dict, files=file_dict)

    assert form.is_valid() == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    'is_program_prereq, is_common_for_all_prereq, is_business_line_prereq, is_valid, errors',
    [
        (False, False, False, True, {}),
        (True, False, False, True, {}),
        (False, True, False, True, {}),
        (False, False, True, True, {}),
        (True, False, True, False, {'is_program_prerequisite': [COURSE_GROUP_PREREQ_VALIDATION_ERROR]}),
        (True, True, False, False, {'is_program_prerequisite': [COURSE_GROUP_PREREQ_VALIDATION_ERROR]}),
        (False, True, True, False, {'is_program_prerequisite': [COURSE_GROUP_PREREQ_VALIDATION_ERROR]}),
        (True, True, True, False, {'is_program_prerequisite': [COURSE_GROUP_PREREQ_VALIDATION_ERROR]})
    ]
)
def test_multilingual_course_group_form_validations(
    is_program_prereq, is_common_for_all_prereq, is_business_line_prereq, is_valid, errors
):
    """
    Test if the prerequisite related validations are working correctly for MultilingualCourseGroupForm
    """
    form_data = {
        'name': 'test',
        'is_program_prerequisite': is_program_prereq,
        'is_common_business_line_prerequisite': is_common_for_all_prereq,
        'business_line_prerequisite': BusinessLineFactory().id if is_business_line_prereq else None
    }

    form = MultilingualCourseGroupForm(data=form_data)
    assert form.errors == errors
    assert form.is_valid() is is_valid
