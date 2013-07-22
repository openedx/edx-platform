"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import unittest
from textwrap import dedent
from mock import Mock, patch

from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from student.models import Registration, UserProfile
from cme_registration.models import CmeUserProfile
from student.tests.factories import UserFactory


class TestCmeRegistration(TestCase):
    """
    Check registration using CME registration functionality
    """

    def setUp(self):

        self.post_vars = {'username': 'testuser',
                          'email': 'test@email.com',
                          'password': '1234',
                          'name': 'Chester Tester',
                          'stanford_affiliated': '1',
                          'how_stanford_affiliated': 'j\'st affiliat\'d',
                          'honor_code': 'true',
                          'terms_of_service': 'true',
                          'profession': 'profession',
                          'professional_designation': 'professional_designation',
                          'license_number': 'license_number',
                          'organization': 'organization',
                          'patient_population': 'patient_population',
                          'specialty': 'specialty',
                          'sub_specialty': 'sub_specialty',
                          'address_1': 'address_1',
                          'address_2': 'address_2',
                          'city': 'city',
                          'state_province': 'state_province',
                          'postal_code': 'postal_code',
                          'country': 'country',
                          'phone_number': 'phone_number',
                          'extension': 'extension',
                          'fax': 'fax',
                          'hear_about_us': 'hear_about_us',
                          'mailing_list': 'false'}

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_badly_formed_message(self):
        """
        Post itself is badly formed
        """

        url = reverse('cme_create_account')
        response = self.client.post(url, {})
        self.assertContains(response, '{"field": "username", "value": "Error (401 username). E-mail us.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_profession_required(self):
        """
        Profession required field
        """

        self.post_vars['profession'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "profession", "value": "Choose your profession.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_license_number_required(self):
        """
        License number required field
        """

        self.post_vars['license_number'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "license_number", "value": "Enter your license number.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_patient_population_required(self):
        """
        Patient population required field
        """

        self.post_vars['patient_population'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "patient_population", "value": "Choose your patient population", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_specialty_required(self):
        """
        Specialty required field
        """

        self.post_vars['specialty'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "specialty", "value": "Choose your specialty", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_sub_specialty_not_required(self):
        """
        Sub specialty not required
        """

        self.post_vars['sub_specialty'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"success": true}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_address_1_required(self):
        """
        Address 1 required field
        """

        self.post_vars['address_1'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "address_1", "value": "Enter your Address 01", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_city_required(self):
        """
        City required field
        """

        self.post_vars['city'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "city", "value": "Enter your city", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_state_province_required(self):
        """
        State Province required field
        """

        self.post_vars['state_province'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "state_province", "value": "Choose your state/Province", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_postal_code_required(self):
        """
        Postal Code required field
        """

        self.post_vars['postal_code'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "postal_code", "value": "Enter your postal code", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_country_required(self):
        """
        Country required field
        """

        self.post_vars['country'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "country", "value": "Choose your country", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_phone_number_required(self):
        """
        Phone number required field
        """

        self.post_vars['phone_number'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "phone_number", "value": "Enter your phone number", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_hear_about_us_required(self):
        """
        Hear about us required field
        """

        self.post_vars['hear_about_us'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "hear_about_us", "value": "Choose how you heard about us", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_specialty_other(self):
        """
        Specialty "other" required field
        """

        self.post_vars['specialty'] = 'Other'
        self.post_vars['specialty_free'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "specialty", "value": "Enter your specialty.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_sub_specialty_other(self):
        """
        Sub specialty "other" required field
        """

        self.post_vars['sub_specialty'] = 'Other'
        self.post_vars['sub_specialty_free'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "sub_specialty", "value": "Enter your sub-specialty.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_hear_about_us_other(self):
        """
        Hear about us "other" required field
        """

        self.post_vars['hear_about_us'] = 'Other'
        self.post_vars['hear_about_us_free'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "hear_about_us", "value": "Enter how you heard about us.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_stanford_affiliated_required(self):
        """
        Stanford affiliated required field
        """

        del self.post_vars['stanford_affiliated']
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "stanford_affiliated", "value": "Select whether, or not, you are affiliated with Stanford.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_honor_code_required(self):
        """
        Honor code required field
        """

        del self.post_vars['honor_code']
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "honor_code", "value": "To enroll, you must follow the honor code.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_tos_required(self):
        """
        TOS required field
        """

        del self.post_vars['terms_of_service']
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "terms_of_service", "value": "You must accept the terms of service.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_stanford_affiliated_choose(self):
        """
        How Stanford affiliated required if stanford affiliated
        """

        self.post_vars['how_stanford_affiliated'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "stanford_affiliated", "value": "Choose how you are affiliated with Stanford.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_stanford_affiliated_other(self):
        """
        Stanford affiliated "other" required field
        """

        self.post_vars['how_stanford_affiliated'] = 'Other'
        self.post_vars['how_stanford_affiliated_free'] = ''
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "how_stanford_affiliated", "value": "Enter how you are affiliated with Stanford.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_db_records_created(self):
        """
        Everything gets created correctly when all input data good
        """

        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        #Check page displays success
        self.assertContains(response, '{"success": true}')

        #Check user was created
        user = User.objects.filter(email='test@email.com')
        self.assertEqual(1, len(user))

        #Check registration was created
        registration = Registration.objects.filter(user=user[0])
        self.assertEqual(1, len(registration))

        #Check cme_user_profile was created
        cme_user_profile = CmeUserProfile.objects.filter(user=user[0],
                                                         name='Chester Tester',
                                                         stanford_affiliated=True,
                                                         how_stanford_affiliated='j\'st affiliat\'d',
                                                         profession='profession',
                                                         professional_designation='professional_designation',
                                                         license_number='license_number',
                                                         organization='organization',
                                                         patient_population='patient_population',
                                                         specialty='specialty',
                                                         sub_specialty='sub_specialty',
                                                         address_1='address_1',
                                                         address_2='address_2',
                                                         city='city',
                                                         state_province='state_province',
                                                         postal_code='postal_code',
                                                         country='country',
                                                         phone_number='phone_number',
                                                         extension='extension',
                                                         fax='fax',
                                                         hear_about_us='hear_about_us',
                                                         mailing_list=False)
        self.assertEqual(1, len(cme_user_profile))

        #Check user_profile was created
        user_profile = UserProfile.objects.filter(user=user[0])
        self.assertEqual(1, len(user_profile))

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_db_records_with_others_created(self):
        """
        Everything gets created correctly when all input data good with "others"
        """

        self.post_vars['how_stanford_affiliated'] = 'Other'
        self.post_vars['how_stanford_affiliated_free'] = 'Wife of the provost'
        self.post_vars['specialty'] = 'Other'
        self.post_vars['specialty_free'] = 'Patient care'
        self.post_vars['sub_specialty'] = 'Other'
        self.post_vars['sub_specialty_free'] = 'Legs and feet'
        self.post_vars['hear_about_us'] = 'Other'
        self.post_vars['hear_about_us_free'] = 'Through the grapevine'
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        #Check page displays success
        self.assertContains(response, '{"success": true}')

        #Check user was created
        user = User.objects.filter(email='test@email.com')
        self.assertEqual(1, len(user))

        #Check registration was created
        registration = Registration.objects.filter(user=user[0])
        self.assertEqual(1, len(registration))

        #Check cme_user_profile was created
        cme_user_profile = CmeUserProfile.objects.filter(user=user[0],
                                                         name='Chester Tester',
                                                         stanford_affiliated=True,
                                                         how_stanford_affiliated='Wife of the provost',
                                                         profession='profession',
                                                         license_number='license_number',
                                                         patient_population='patient_population',
                                                         specialty='Patient care',
                                                         sub_specialty='Legs and feet',
                                                         address_1='address_1',
                                                         city='city',
                                                         state_province='state_province',
                                                         postal_code='postal_code',
                                                         country='country',
                                                         phone_number='phone_number',
                                                         hear_about_us='Through the grapevine')
        self.assertEqual(1, len(cme_user_profile))

        #Check user_profile was created
        user_profile = UserProfile.objects.filter(user=user[0])
        self.assertEqual(1, len(user_profile))

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_valid_email(self):
        """
        Email address conforms
        """

        self.post_vars['email'] = 'garbage_email_string'
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "email", "value": "Valid e-mail is required.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_valid_username(self):
        """
        Username conforms
        """

        self.post_vars['username'] = ' $%$%$# '
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "username", "value": "Username should only consist of A-Z and 0-9, with no spaces.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_dupe_username(self):
        """
        Username not already existing
        """

        UserFactory.create(username="student001", email="student001@test.com")

        self.post_vars['username'] = 'student001'
        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "username", "value": "An account with the Public Username  \'student001\' already exists.", "success": false}')

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_register_when_logged_in(self):
        """
        Must be logged out to register
        """

        user = UserFactory.create(username="student002", email="student002@test.com")
        self.client.login(username=user.username, password='test')

        url = reverse('cme_register_user')
        response = self.client.post(url, {})
        self.assertRedirects(response, reverse('dashboard'), status_code=302)

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_register_page_loads(self):
        """
        CME Register page itself renders
        """

        url = reverse('cme_register_user')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_reroute_activation_email(self):
        """
        Registration successful with reroute activation email true
        """

        settings.MITX_FEATURES['REROUTE_ACTIVATION_EMAIL'] = 'a@b.edu'

        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        #Check page displays success
        self.assertContains(response, '{"success": true}')

    @patch('cme_registration.models.CmeUserProfile.save', Mock(side_effect=Exception()))
    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_save_profile_exception(self):
        """
        Profile doesn't get created on exception
        """

        url = reverse('cme_create_account')
        self.client.post(url, self.post_vars)

        cme_user_profile = CmeUserProfile.objects.filter(name='Chester Tester')
        self.assertEqual(0, len(cme_user_profile))

    @patch('django.contrib.auth.models.User.email_user', Mock(side_effect=Exception()))
    @unittest.skipUnless(not settings.MITX_FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                         dedent("""Skipping Test because the url is not in CMS"""))
    def test_activation_email_exception(self):
        """
        Exception if activation email not sent
        """

        url = reverse('cme_create_account')
        response = self.client.post(url, self.post_vars)

        self.assertRaises(Exception)
        self.assertContains(response, 'Could not send activation e-mail.')
