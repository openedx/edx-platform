"""
All tests for applications views
"""
from datetime import date, timedelta
from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase

from openedx.adg.lms.applications.constants import DAYS_PER_YEAR
from openedx.adg.lms.applications.forms import ContactInformationForm


class ContactInformationFormTest(TestCase):
    """
    Test cases for the ContactInformationForm
    """

    def contact_information_dictionary(self, gender='male', phone_number='00000000',
                                       birth_day=None, birth_month=None, birth_year=None,
                                       organization='test', linkedin_url=''):
        """
        Initialize the data dictionary for contact information forms
        """
        return {
            'gender': gender,
            'phone_number': phone_number,
            'birth_day': birth_day,
            'birth_month': birth_month,
            'birth_year': birth_year,
            'organization': organization,
            'linkedin_url': linkedin_url
        }

    def setUp(self):
        """
        Setup a new user to POST the data
        """
        self.user = get_user_model().objects.create_user(
            email='testuser@test.com',
            password='password',
            username='testuser'
        )

    def test_contact_info_form_with_future_birth_date(self):
        """
        Verify that future dates are not allowed in birth_date field
        """
        tomorrow = date.today() + timedelta(days=1)
        data = self.contact_information_dictionary(birth_day=str(tomorrow.day),
                                                   birth_month=str(tomorrow.month), birth_year=str(tomorrow.year))
        form = ContactInformationForm(data=data)
        self.assertFalse(form.is_valid())

    def test_contact_info_form_with_minimum_valid_age(self):
        """
        Verify that birth_date with at least 21 year difference is allowed
        """
        years = 21
        minimum_age = date.today() - timedelta(days=(years * DAYS_PER_YEAR + 1))
        data = self.contact_information_dictionary(birth_day=str(minimum_age.day),
                                                   birth_month=str(minimum_age.month), birth_year=str(minimum_age.year))
        form = ContactInformationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_contact_info_form_with_minimum_invalid_age(self):
        """
        Verify that birth_date with at least 21 year difference is allowed
        """
        years = 21
        minimum_age = date.today() - timedelta(days=(years * DAYS_PER_YEAR))
        data = self.contact_information_dictionary(birth_day=str(minimum_age.day),
                                                   birth_month=str(minimum_age.month), birth_year=str(minimum_age.year))
        form = ContactInformationForm(data=data)
        self.assertFalse(form.is_valid())

    def test_contact_info_form_with_maximum_valid_age(self):
        """
        Verify that birth_date with difference greater than 60 year is not allowed
        """
        years = 61
        minimum_age = date.today() - timedelta(days=(years * DAYS_PER_YEAR))
        data = self.contact_information_dictionary(birth_day=str(minimum_age.day),
                                                   birth_month=str(minimum_age.month), birth_year=str(minimum_age.year))
        form = ContactInformationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_contact_info_form_with_maximum_invalid_age(self):
        """
        Verify that birth_date with difference greater than 60 year is not allowed
        """
        years = 61
        minimum_age = date.today() - timedelta(days=(years * DAYS_PER_YEAR + 1))
        data = self.contact_information_dictionary(birth_day=str(minimum_age.day),
                                                   birth_month=str(minimum_age.month), birth_year=str(minimum_age.year))
        form = ContactInformationForm(data=data)
        self.assertFalse(form.is_valid())

    @pytest.mark.django_db
    def test_contact_info_form_valid_data(self):
        """
        Verify that valid data is stored in database successfully
        """
        birth_date = date.today() - timedelta(days=(30 * DAYS_PER_YEAR))
        data = self.contact_information_dictionary(birth_day=str(birth_date.day),
                                                   birth_month=str(birth_date.month), birth_year=str(birth_date.year))
        form = ContactInformationForm(data=data)
        mocked_request = Mock()
        mocked_request.user = self.user
        if form.is_valid():
            form.save(request=mocked_request)
        self.assertEqual(data.get('gender'), self.user.profile.gender)
        self.assertEqual(data.get('phone_number'), self.user.profile.phone_number)
        self.assertEqual(data.get('organization'), self.user.application.organization)
        self.assertEqual(data.get('linkedin_url'), self.user.application.linkedin_url)
        self.assertEqual(birth_date, self.user.extended_profile.birth_date)
