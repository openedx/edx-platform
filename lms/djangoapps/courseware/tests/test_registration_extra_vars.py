# -*- coding: utf-8
"""
Tests for extra registration variables
"""
import json
import uuid

from django.conf import settings
from django.core.urlresolvers import reverse
from mock import patch

from courseware.tests.helpers import LoginEnrollmentTestCase, check_for_post_code


class TestExtraRegistrationVariables(LoginEnrollmentTestCase):
    """
    Test that extra registration variables are properly checked according to settings
    """

    def _do_register_attempt(self, **extra_fields_values):
        """
        Helper method to make the call to the do registration
        """
        username = 'foo_bar' + uuid.uuid4().hex
        fields_values = {
            'username': username,
            'email': 'foo' + uuid.uuid4().hex + '@bar.com',
            'password': 'password',
            'name': username,
            'terms_of_service': 'true',
        }
        fields_values = dict(fields_values.items() + extra_fields_values.items())
        resp = check_for_post_code(self, 200, reverse('create_account'), fields_values)
        data = json.loads(resp.content)
        return data

    def test_default_missing_honor(self):
        """
        By default, the honor code must be required
        """
        data = self._do_register_attempt(honor_code='')
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], u'To enroll, you must follow the honor code.')

    @patch.dict(settings.REGISTRATION_EXTRA_FIELDS, {'honor_code': 'optional'})
    def test_optional_honor(self):
        """
        With the honor code is made optional, should pass without extra vars
        """
        data = self._do_register_attempt(honor_code='')
        self.assertEqual(data['success'], True)

    @patch.dict(settings.REGISTRATION_EXTRA_FIELDS, {
        'level_of_education': 'hidden',
        'gender': 'hidden',
        'year_of_birth': 'hidden',
        'mailing_address': 'hidden',
        'goals': 'hidden',
        'honor_code': 'hidden',
        'city': 'hidden',
        'country': 'hidden'})
    def test_all_hidden(self):
        """
        When the fields are all hidden, should pass without extra vars
        """
        data = self._do_register_attempt()
        self.assertEqual(data['success'], True)

    @patch.dict(settings.REGISTRATION_EXTRA_FIELDS, {'city': 'required'})
    def test_required_city_missing(self):
        """
        Should require the city if configured as 'required' but missing
        """
        data = self._do_register_attempt(honor_code='true', city='')
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], u'A city is required')

        data = self._do_register_attempt(honor_code='true', city='New York')
        self.assertEqual(data['success'], True)

    @patch.dict(settings.REGISTRATION_EXTRA_FIELDS, {'country': 'required'})
    def test_required_country_missing(self):
        """
        Should require the country if configured as 'required' but missing
        """
        data = self._do_register_attempt(honor_code='true', country='')
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], u'A country is required')

        data = self._do_register_attempt(honor_code='true', country='New York')
        self.assertEqual(data['success'], True)

    @patch.dict(settings.REGISTRATION_EXTRA_FIELDS, {'level_of_education': 'required'})
    def test_required_level_of_education_missing(self):
        """
        Should require the level_of_education if configured as 'required' but missing
        """
        data = self._do_register_attempt(honor_code='true', level_of_education='')
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], u'A level of education is required.')

        data = self._do_register_attempt(honor_code='true', level_of_education='p')
        self.assertEqual(data['success'], True)

    @patch.dict(settings.REGISTRATION_EXTRA_FIELDS, {'gender': 'required'})
    def test_required_gender_missing(self):
        """
        Should require the gender if configured as 'required' but missing
        """
        data = self._do_register_attempt(honor_code='true', gender='')
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], u'Your gender is required')

        data = self._do_register_attempt(honor_code='true', gender='m')
        self.assertEqual(data['success'], True)

    @patch.dict(settings.REGISTRATION_EXTRA_FIELDS, {'year_of_birth': 'required'})
    def test_required_year_of_birth_missing(self):
        """
        Should require the year_of_birth if configured as 'required' but missing
        """
        data = self._do_register_attempt(honor_code='true', year_of_birth='')
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], u'Your year of birth is required')

        data = self._do_register_attempt(honor_code='true', year_of_birth='1982')
        self.assertEqual(data['success'], True)

    @patch.dict(settings.REGISTRATION_EXTRA_FIELDS, {'mailing_address': 'required'})
    def test_required_mailing_address_missing(self):
        """
        Should require the mailing_address if configured as 'required' but missing
        """
        data = self._do_register_attempt(honor_code='true', mailing_address='')
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], u'Your mailing address is required')

        data = self._do_register_attempt(honor_code='true', mailing_address='my address')
        self.assertEqual(data['success'], True)

    @patch.dict(settings.REGISTRATION_EXTRA_FIELDS, {'goals': 'required'})
    def test_required_goals_missing(self):
        """
        Should require the goals if configured as 'required' but missing
        """
        data = self._do_register_attempt(honor_code='true', goals='')
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], u'A description of your goals is required')

        data = self._do_register_attempt(honor_code='true', goals='my goals')
        self.assertEqual(data['success'], True)
