"""
All tests for applications views
"""
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from dateutil.relativedelta import relativedelta

from openedx.adg.lms.applications.admin import UserApplicationADGAdmin
from openedx.adg.lms.applications.constants import (
    APPLICATION_REVIEW_ERROR_MSG,
    COURSE_GROUP_PREREQ_VALIDATION_ERROR,
    MAX_NUMBER_OF_WORDS_ALLOWED_IN_TEXT_INPUT,
    MAXIMUM_AGE_LIMIT,
    MINIMUM_AGE_LIMIT
)
from openedx.adg.lms.applications.forms import (
    BusinessLineInterestForm,
    ExtendedUserProfileForm,
    MultilingualCourseGroupForm
)
from openedx.adg.lms.registration_extension.tests.factories import ExtendedUserProfileFactory

from .constants import TEST_INTEREST_IN_BUSINESS, VALID_USER_BIRTH_DATE_FOR_APPLICATION
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


@pytest.mark.parametrize('age_year , expected', [
    (MINIMUM_AGE_LIMIT - 1, False), (MINIMUM_AGE_LIMIT, True), (MAXIMUM_AGE_LIMIT, True), (MAXIMUM_AGE_LIMIT + 1, False)
])
def test_extended_user_profile_form_with_birth_date(age_year, expected):
    """
    Test that the age limit is validated correctly
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


# ------- Business Line Interest Form tests below -------


@pytest.mark.django_db
@pytest.mark.parametrize(
    'business_line, interest_in_business, button_click, expected',
    [
        (None, TEST_INTEREST_IN_BUSINESS, 'back', True),
        (None, None, 'back', True),
        ('business', TEST_INTEREST_IN_BUSINESS, 'back', True),
        ('business', None, 'back', True),
        (None, TEST_INTEREST_IN_BUSINESS, 'submit', False),
        (None, None, 'submit', False),
        ('business', TEST_INTEREST_IN_BUSINESS, 'submit', True),
        ('business', None, 'submit', False)
    ],
    ids=[
        'back_button_clicked_with_interest_text_and_no_business_line',
        'back_button_clicked_with_no_interest_text_and_no_business_line',
        'back_button_clicked_with_business_line_and_interest_text',
        'back_button_clicked_with_business_line_and_no_interest_text',
        'submit_button_clicked_with_interest_text_and_no_business_line',
        'submit_button_clicked_with_with_no_interest_text_and_no_business_line',
        'submit_button_clicked_with_interest_text_and_business_line',
        'submit_button_clicked_with_business_line_and_no_interest_text',
    ]
)
def test_business_line_interest_form_validations(
    business_line, interest_in_business, button_click, expected
):
    """
    Validate that business line is a compulsory field
    """
    if business_line == 'business':
        business_line = BusinessLineFactory().id

    data_dict = {
        'business_line': business_line,
        'submit_or_back_clicked': button_click,
        'interest_in_business': interest_in_business,
    }

    form = BusinessLineInterestForm(data=data_dict)
    assert form.is_valid() == expected


@pytest.mark.django_db
@pytest.mark.parametrize('button_click, interest_in_business, expected', [
    ('back', '', True),
    ('back', TEST_INTEREST_IN_BUSINESS, True),
    ('back', TEST_INTEREST_IN_BUSINESS * MAX_NUMBER_OF_WORDS_ALLOWED_IN_TEXT_INPUT, False),
    ('submit', '', False),
    ('submit', TEST_INTEREST_IN_BUSINESS, True),
    ('submit', TEST_INTEREST_IN_BUSINESS * MAX_NUMBER_OF_WORDS_ALLOWED_IN_TEXT_INPUT, False),
])
def test_business_line_interest_form_interest_in_buiness_field_validations(
    button_click, interest_in_business, expected
):
    """
    Validate that interest_in_business field is compulsory and has a max word limit
    """
    data_dict = {
        'business_line': BusinessLineFactory().id,
        'submit_or_back_clicked': button_click,
        'interest_in_business': interest_in_business,
    }

    form = BusinessLineInterestForm(data=data_dict)
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
