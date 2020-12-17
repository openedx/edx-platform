"""
All tests for applications views
"""
from datetime import date, timedelta
from unittest.mock import Mock

import pytest
from dateutil.relativedelta import relativedelta

from openedx.adg.lms.applications.forms import ContactInformationForm
from openedx.adg.lms.applications.test.factories import ExtendedProfileFactory, ProfileFactory, UserFactory


def contact_information_dictionary(name='test', email='test@example.com', city='XYZ',
                                   gender='male', phone_number='00000000',
                                   birth_day=None, birth_month=None, birth_year=None,
                                   organization='test', linkedin_url=''):
    """
    Initialize the data dictionary for contact information forms
    """
    return {
        'name': name,
        'email': email,
        'city': city,
        'saudi_national': True,
        'gender': gender,
        'phone_number': phone_number,
        'birth_day': birth_day,
        'birth_month': birth_month,
        'birth_year': birth_year,
        'organization': organization,
        'linkedin_url': linkedin_url
    }


@pytest.mark.django_db
def create_factories():
    """
    Create user and related factories
    """
    user = UserFactory.create()

    profile = ProfileFactory()
    profile.user = user
    profile.save()

    extended_profile = ExtendedProfileFactory()
    extended_profile.user = user
    extended_profile.save()
    return user


def test_contact_info_form_with_future_birth_date():
    """
    Verify that future dates are not allowed in birth_date field
    """
    tomorrow = date.today() + timedelta(days=1)
    data = contact_information_dictionary(birth_day=str(tomorrow.day),
                                          birth_month=str(tomorrow.month), birth_year=str(tomorrow.year))
    form = ContactInformationForm(data=data)
    assert not form.is_valid()


@pytest.mark.parametrize("age_year , expected", [(21, True), (61, False)])
def test_contact_info_form_with_birth_date(age_year, expected):
    """
    Verify that birth_date with at least 21 year difference is allowed
    """
    age = date.today() - relativedelta(years=age_year)
    data = contact_information_dictionary(birth_day=str(age.day),
                                          birth_month=str(age.month), birth_year=str(age.year))
    form = ContactInformationForm(data=data)
    assert form.is_valid() == expected


@pytest.mark.django_db
def test_contact_info_form_valid_data():
    """
    Verify that valid data is stored in database successfully
    """
    birth_date = date.today() - relativedelta(years=30)
    user = create_factories()
    data = contact_information_dictionary(birth_day=str(birth_date.day),
                                          birth_month=str(birth_date.month), birth_year=str(birth_date.year))
    form = ContactInformationForm(data=data)
    mocked_request = Mock()
    mocked_request.user = user
    if form.is_valid():
        form.save(request=mocked_request)
    user.profile.refresh_from_db()
    user.extended_profile.refresh_from_db()
    assert data.get('gender') == user.profile.gender
    assert data.get('phone_number') == user.profile.phone_number
    assert data.get('organization') == user.application.organization
    assert data.get('linkedin_url') == user.application.linkedin_url
    assert birth_date == user.extended_profile.birth_date
