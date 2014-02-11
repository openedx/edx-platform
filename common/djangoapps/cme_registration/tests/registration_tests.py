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
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from student.models import Registration, UserProfile
from cme_registration.models import CmeUserProfile
from student.tests.factories import UserFactory
from cme_registration.views import DENIED_COUNTRIES, validate_export_controls, setup_sub_affiliation_field
TEST_FEATURES = settings.FEATURES.copy()
TEST_FEATURES['USE_CME_REGISTRATION'] = True


@override_settings(FEATURES=TEST_FEATURES)
class TestCmeRegistration(TestCase):
    """
    Check registration using CME registration functionality
    """

    def setUp(self):

        self.post_vars = {'username': 'testuser',
                          'email': 'test@email.com',
                          'password': '1234',
                          'name': 'Chester Tester',
                          'first_name': 'Chester',
                          'last_name': 'Tester',
                          'middle_initial': 'A',
                          'birth_date': '09/24',
                          'honor_code': 'true',
                          'terms_of_service': 'true',
                          'professional_designation': 'professional_designation',
                          'license_number': 'license_number',
                          'license_country': 'license_country',
                          'license_state': 'license_state',
                          'physician_status': 'physician_status',
                          'patient_population': 'patient_population',
                          'specialty': 'specialty',
                          'sub_specialty': 'sub_specialty',
                          'affiliation': 'affiliation',
                          'other_affiliation': 'other_affiliation',
                          'sub_affiliation': 'sub_affiliation',
                          'sunet_id': 'sunet_id',
                          'stanford_department': 'stanford_department',
                          'address_1': 'address_1',
                          'address_2': 'address_2',
                          'city': 'city',
                          'state': 'state',
                          'postal_code': 'postal_code',
                          'country': 'country',
                          'county_province': 'county_province',
                          }

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_badly_formed_message(self):

        url = reverse('create_account')
        response = self.client.post(url, {})
        self.assertContains(response, '{"field": "username", "value": "Error (401 username). E-mail us.", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_last_name_required(self):

        self.post_vars['last_name'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "last_name", "value": "Enter your last name", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_first_name_required(self):

        self.post_vars['first_name'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "first_name", "value": "Enter your first name", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_middle_initial_length(self):

        self.post_vars['middle_initial'] = 'ABC'
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "middle_initial", "value": "Enter your middle initial as a single character", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_birth_date_required(self):

        self.post_vars['birth_date'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "birth_date", "value": "Enter your birth date", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_birth_date_format1(self):

        self.post_vars['birth_date'] = '0102'
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "birth_date", "value": "Enter your birth date as MM/DD", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_birth_date_format2(self):

        self.post_vars['birth_date'] = '14/02'
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "birth_date", "value": "month must be in 1..12", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_professional_designation_required(self):

        self.post_vars['professional_designation'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "professional_designation", "value": "Choose your professional designation", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_license_number_required(self):

        self.post_vars['professional_designation'] = 'DO'
        self.post_vars['license_number'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "license_number", "value": "Enter your license number", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_license_country_required(self):

        self.post_vars['professional_designation'] = 'DO'
        self.post_vars['license_country'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "license_country", "value": "Choose your license country", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_license_state_required(self):

        self.post_vars['license_country'] = 'United States'
        self.post_vars['license_state'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "license_state", "value": "Choose your license state", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_physician_status_required(self):

        self.post_vars['professional_designation'] = 'DO'
        self.post_vars['physician_status'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "physician_status", "value": "Enter your physician status", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_patient_population_required(self):

        self.post_vars['professional_designation'] = 'DO'
        self.post_vars['patient_population'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "patient_population", "value": "Choose your patient population", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_specialty_required(self):

        self.post_vars['professional_designation'] = 'DO'
        self.post_vars['specialty'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "specialty", "value": "Choose your specialty", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_sub_specialty_not_required(self):

        self.post_vars['sub_specialty'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '"success": true')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_sub_affiliation_field(self):

        self.post_vars['affiliation'] = 'Packard Children\'s Health Alliance'
        self.post_vars['PCHA_affiliation'] = 'Dummy_Value1'

        return_vars = setup_sub_affiliation_field(self.post_vars)
        self.assertEquals(return_vars['sub_affiliation'], 'Dummy_Value1')

        self.post_vars['affiliation'] = 'University Healthcare Alliance'
        self.post_vars['UHA_affiliation'] = 'Dummy_Value2'

        return_vars = setup_sub_affiliation_field(self.post_vars)
        self.assertEquals(return_vars['sub_affiliation'], 'Dummy_Value2')

        self.post_vars['affiliation'] = 'Lucile Packard Children\'s Hospital'
        self.post_vars['PCHA_affiliation'] = 'Dummy_Value1'
        self.post_vars['UHA_affiliation'] = 'Dummy_Value2'

        return_vars = setup_sub_affiliation_field(self.post_vars)
        self.assertEquals(return_vars['sub_affiliation'], '')

        self.post_vars['affiliation'] = 'Packard Children\'s Health Alliance'
        self.post_vars['PCHA_affiliation'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "sub_affiliation", "value": "Enter your Packard Children\'s Health Alliance affiliation", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_sunet_id_required(self):

        self.post_vars['affiliation'] = 'Stanford University'
        self.post_vars['sunet_id'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "sunet_id", "value": "Enter your SUNet ID", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_stanford_department_required(self):

        self.post_vars['affiliation'] = 'Stanford University'
        self.post_vars['stanford_department'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "stanford_department", "value": "Choose your Stanford department", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_address_1_required(self):

        self.post_vars['address_1'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "address_1", "value": "Enter your Address 1", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_city_required(self):

        self.post_vars['city'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "city", "value": "Enter your city", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_country_required(self):

        self.post_vars['country'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "country", "value": "Choose your country", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_state_required(self):

        self.post_vars['country'] = 'United States'
        self.post_vars['state'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "state", "value": "Choose your state", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_postal_code_required(self):

        self.post_vars['postal_code'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "postal_code", "value": "Enter your postal code", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_specialty_other(self):

        self.post_vars['specialty'] = 'Other'
        self.post_vars['specialty_free'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "specialty", "value": "Enter your specialty.", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_sub_specialty_other(self):

        self.post_vars['sub_specialty'] = 'Other'
        self.post_vars['sub_specialty_free'] = ''
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "sub_specialty", "value": "Enter your sub-specialty.", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_honor_code_required(self):

        del self.post_vars['honor_code']
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "honor_code", "value": "To enroll, you must follow the honor code.", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_tos_required(self):

        del self.post_vars['terms_of_service']
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "terms_of_service", "value": "You must accept the terms of service.", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_db_records_created(self):

        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        #Check page displays success
        self.assertContains(response, '"success": true')

        #Check user was created
        user = User.objects.filter(email='test@email.com')
        self.assertEqual(1, len(user))

        #Check registration was created
        registration = Registration.objects.filter(user=user[0])
        self.assertEqual(1, len(registration))

        #Check cme_user_profile was created
        cme_user_profile = CmeUserProfile.objects.filter(user=user[0],
                                                         name='Chester Tester',
                                                         first_name='Chester',
                                                         last_name='Tester',
                                                         middle_initial='A',
                                                         birth_date='09/24',
                                                         professional_designation='professional_designation',
                                                         license_number='license_number',
                                                         license_country='license_country',
                                                         license_state='license_state',
                                                         physician_status='physician_status',
                                                         patient_population='patient_population',
                                                         specialty='specialty',
                                                         sub_specialty='sub_specialty',
                                                         affiliation='affiliation',
                                                         sub_affiliation='',
                                                         sunet_id='sunet_id',
                                                         stanford_department='stanford_department',
                                                         address_1='address_1',
                                                         address_2='address_2',
                                                         city_cme='city',
                                                         state='state',
                                                         postal_code='postal_code',
                                                         country_cme='country',
                                                         county_province='county_province'
                                                         )

        self.assertEqual(1, len(cme_user_profile))

        #Check user_profile was created
        user_profile = UserProfile.objects.filter(user=user[0])
        self.assertEqual(1, len(user_profile))

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_db_records_with_others_created(self):

        self.post_vars['specialty'] = 'Other'
        self.post_vars['specialty_free'] = 'Patient care'
        self.post_vars['sub_specialty'] = 'Other'
        self.post_vars['sub_specialty_free'] = 'Legs and feet'
        self.post_vars['affiliation'] = 'Other'
        self.post_vars['other_affiliation'] = 'other_affiliation'
        self.post_vars['sub_affiliation'] = ''

        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        #Check page displays success
        self.assertContains(response, '"success": true')

        #Check user was created
        user = User.objects.filter(email='test@email.com')
        self.assertEqual(1, len(user))

        #Check registration was created
        registration = Registration.objects.filter(user=user[0])
        self.assertEqual(1, len(registration))

        #Check cme_user_profile was created
        cme_user_profile = CmeUserProfile.objects.filter(user=user[0],
                                                         name='Chester Tester',
                                                         first_name='Chester',
                                                         last_name='Tester',
                                                         middle_initial='A',
                                                         birth_date='09/24',
                                                         professional_designation='professional_designation',
                                                         license_number='license_number',
                                                         license_country='license_country',
                                                         license_state='license_state',
                                                         physician_status='physician_status',
                                                         patient_population='patient_population',
                                                         affiliation='Other',
                                                         other_affiliation='other_affiliation',
                                                         sub_affiliation='',
                                                         sunet_id='sunet_id',
                                                         stanford_department='stanford_department',
                                                         address_1='address_1',
                                                         address_2='address_2',
                                                         city_cme='city',
                                                         state='state',
                                                         postal_code='postal_code',
                                                         country_cme='country',
                                                         county_province='county_province',
                                                         specialty='Patient care',
                                                         sub_specialty='Legs and feet',
                                                         )
        self.assertEqual(1, len(cme_user_profile))

        #Check user_profile was created
        user_profile = UserProfile.objects.filter(user=user[0])
        self.assertEqual(1, len(user_profile))

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_valid_email(self):

        self.post_vars['email'] = 'garbage_email_string'
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "email", "value": "Valid e-mail is required.", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_valid_username(self):

        self.post_vars['username'] = ' $%$%$# '
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "username", "value": "Username should only consist of A-Z and 0-9, with no spaces.", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_dupe_username(self):

        UserFactory.create(username="student001", email="student001@test.com")

        self.post_vars['username'] = 'student001'
        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertContains(response, '{"field": "username", "value": "An account with the Public Username  \'student001\' already exists.", "success": false}')

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_register_when_logged_in(self):

        user = UserFactory.create(username="student002", email="student002@test.com")
        self.client.login(username=user.username, password='test')

        url = reverse('register_user')
        response = self.client.post(url, {})
        self.assertRedirects(response, reverse('dashboard'), status_code=302)

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_register_page_loads(self):

        url = reverse('register_user')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)

    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_reroute_activation_email(self):

        settings.FEATURES['REROUTE_ACTIVATION_EMAIL'] = 'a@b.edu'

        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        #Check page displays success
        self.assertContains(response, '"success": true')

    @patch('cme_registration.models.CmeUserProfile.save', Mock(side_effect=Exception()))
    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_save_profile_exception(self):

        url = reverse('create_account')
        self.client.post(url, self.post_vars)

        cme_user_profile = CmeUserProfile.objects.filter(name='Chester Tester')
        self.assertEqual(0, len(cme_user_profile))

    @patch('django.contrib.auth.models.User.email_user', Mock(side_effect=Exception()))
    @unittest.skipIf(settings.FEATURES.get('DISABLE_CME_REGISTRATION_TESTS', False),
                     dedent("""Skipping Test because the url is not in CMS"""))
    def test_activation_email_exception(self):

        url = reverse('create_account')
        response = self.client.post(url, self.post_vars)

        self.assertRaises(Exception)
        self.assertContains(response, 'Could not send activation e-mail.')

    def test_export_controls(self):

        for country in DENIED_COUNTRIES:
            retv = validate_export_controls({'country': country})
            self.assertFalse(retv['success'])
            self.assertEqual(retv['field'], 'country')

        self.assertIsNone(validate_export_controls({'country': 'United States'}))
