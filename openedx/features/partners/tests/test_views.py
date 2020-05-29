import mock

from ddt import data, ddt
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from lms.djangoapps.onboarding.models import Organization, UserExtendedProfile
from openedx.core.lib.api.test_utils import ApiTestCase
from openedx.features.partners.constants import PARTNER_USER_STATUS_WAITING
from openedx.features.partners.models import PartnerUser
from openedx.features.partners.tests.factories import FocusAreaFactory, OrganizationFactory, PartnerFactory
from openedx.features.philu_utils.tests.mixins import PhiluThemeMixin


@ddt
class PartnerRegistrationViewTest(PhiluThemeMixin, ApiTestCase):
    """
    Includes test cases for partner registration
    """

    NAME = 'bob23 james'
    COUNTRY = 'PK'
    ORGANIZATION = 'arbisoft'
    EMAIL = 'bob@example.com'
    USERNAME = 'bob123'
    PASSWORD = 'Test@12345'
    TERMS_OF_SERVICE = True
    PARTNER = 'give2asia'

    def setUp(self):
        self.partner = PartnerFactory.create(slug=self.PARTNER,
                                             label=self.ORGANIZATION)
        self.registration_url = reverse('partner_register', args=[self.PARTNER])
        self.partner_url = reverse('partner_url', args=[self.PARTNER])

    def test_create_new_partner_landing_page_is_accessible(self):
        """
        Test that on creating new partner the landing page is accessible
        :return : None
        """
        response = self.client.get(self.partner_url)
        self.assertHttpOK(response)

    def test_put_not_allowed(self):
        """
        API should not accept http put method
        :return : None
        """
        response = self.client.put(self.registration_url)
        self.assertHttpMethodNotAllowed(response)

    def test_delete_not_allowed(self):
        """
        API should not accept http delete method
        :return : None
        """
        response = self.client.delete(self.registration_url)
        self.assertHttpMethodNotAllowed(response)

    def test_create_new_partner_user_with_orphan_organization(self):
        """
        Test user is first learner for already existing orphan organization
        Create an organization and then try to register.
        :return : None
        """
        OrganizationFactory(label=self.ORGANIZATION)

        response = self.client.post(self.registration_url, {
            'name': self.NAME,
            'organization_name': self.ORGANIZATION,
            'country': self.COUNTRY,
            'email': self.EMAIL,
            'username': self.USERNAME,
            'password': self.PASSWORD,
            'terms_of_service': self.TERMS_OF_SERVICE
        })
        self.assertHttpOK(response)

        # get inserted data from the database
        user = User.objects.filter(username=self.USERNAME).first()
        organization = Organization.objects.filter(label__iexact=self.ORGANIZATION).first()
        extended_profile = UserExtendedProfile.objects.filter(user=user).first()

        # verify if user is registered and data is stored in the database
        self.assertIsNotNone(user)
        self.assertEqual(self.USERNAME, user.username)
        self.assertEqual(self.EMAIL, user.email)
        self.assertEqual(self.NAME.split(' ', 1)[0], user.first_name)
        self.assertEqual(self.NAME.split(' ', 1)[1], user.last_name)
        self.assertTrue(user.is_active)
        self.assertEqual(self.ORGANIZATION, organization.label)
        # in case organization already exists make sure that user is not first learner
        self.assertTrue(extended_profile.is_first_learner)
        self.assertHttpOK(response)

    @mock.patch('openedx.features.partners.views.Organization.can_join_as_first_learner')
    def test_create_new_partner_user_with_non_orphan_organization(self, mock_can_join_as_first_learner):
        """
        Test user is not first learner if organization already exists with some members
        Create an organization and then try to register.
        :return : None
        """
        OrganizationFactory(label=self.ORGANIZATION)
        mock_can_join_as_first_learner.return_value = False

        response = self.client.post(self.registration_url, {
            'name': self.NAME,
            'organization_name': self.ORGANIZATION,
            'country': self.COUNTRY,
            'email': self.EMAIL,
            'username': self.USERNAME,
            'password': self.PASSWORD,
            'terms_of_service': self.TERMS_OF_SERVICE
        })
        self.assertHttpOK(response)

        # get inserted data from the database
        user = User.objects.filter(username=self.USERNAME).first()
        organization = Organization.objects.filter(label__iexact=self.ORGANIZATION).first()
        extended_profile = UserExtendedProfile.objects.filter(user=user).first()

        # verify if user is registered and data is stored in the database
        self.assertIsNotNone(user)
        self.assertEqual(self.USERNAME, user.username)
        self.assertEqual(self.EMAIL, user.email)
        self.assertEqual(self.NAME.split(' ', 1)[0], user.first_name)
        self.assertEqual(self.NAME.split(' ', 1)[1], user.last_name)
        self.assertTrue(user.is_active)
        self.assertEqual(self.ORGANIZATION, organization.label)
        # in case organization already exists make sure that user is not first learner
        self.assertFalse(extended_profile.is_first_learner)
        self.assertHttpOK(response)

    def test_create_new_partner_user_with_new_organization(self):
        """
        Test user is first learner if new organization is added
        If organization does not exists system will create a new
        one and add user to it and mark the user as a new learner.
        :return : None
        """
        # create focus area with default values
        FocusAreaFactory()

        response = self.client.post(self.registration_url, {
            'name': self.NAME,
            'organization_name': self.ORGANIZATION,
            'country': self.COUNTRY,
            'email': self.EMAIL,
            'username': self.USERNAME,
            'password': self.PASSWORD,
            'terms_of_service': self.TERMS_OF_SERVICE
        })
        self.assertHttpOK(response)

        # get inserted data from the database
        user = User.objects.filter(username=self.USERNAME).first()
        organization = Organization.objects.filter(label__iexact=self.ORGANIZATION).first()
        extended_profile = UserExtendedProfile.objects.filter(user=user).first()

        # verify if user is registered and data is stored in the database
        self.assertIsNotNone(user)
        self.assertEqual(self.USERNAME, user.username)
        self.assertEqual(self.EMAIL, user.email)
        self.assertEqual(self.NAME.split(' ', 1)[0], user.first_name)
        self.assertEqual(self.NAME.split(' ', 1)[1], user.last_name)
        self.assertTrue(user.is_active)
        self.assertEqual(organization.label, organization.label)
        # in case of new organization make sure that user is created as first learner
        self.assertTrue(extended_profile.is_first_learner)
        self.assertHttpOK(response)

    @data(
        {'name': ''},
        {'country': ''},
        {'email': ''},
        {'username': ''},
        {'password': 'invalid'},
        {'terms_of_service': ''}
    )
    def test_register_invalid_input(self, invalid_fields):
        """
        Test registration is failed if invalid user data is provided
        :param invalid_fields: field to be override with invalid data
        :return: None
        """
        # Initially, the field values are all valid
        form_data = {
            'name': self.NAME,
            'organization_name': self.ORGANIZATION,
            'country': self.COUNTRY,
            'email': self.EMAIL,
            'username': self.USERNAME,
            'password': self.PASSWORD,
            'terms_of_service': self.TERMS_OF_SERVICE
        }
        # Override the valid fields, making the input invalid
        form_data.update(invalid_fields)

        # Attempt to create the partner user, expecting an error response
        response = self.client.post(self.registration_url, form_data)
        self.assertHttpBadRequest(response)

    @data('username', 'country', 'password', 'email', 'terms_of_service')
    def test_register_missing_required_field(self, missing_field):
        """
        Test registration is failed if one of required field is missing
        :param missing_field: field to be deleted from input data
        :return: None
        """
        form_data = {
            'username': self.USERNAME,
            'password': self.PASSWORD,
            'email': self.EMAIL,
            'name': self.NAME,
            'country': self.COUNTRY,
            'organization_name': self.ORGANIZATION,
            'terms_of_service': self.TERMS_OF_SERVICE
        }

        # delete required field
        if missing_field in form_data:
            del form_data[missing_field]

        # Send a request with missing field
        response = self.client.post(self.registration_url, form_data)
        self.assertHttpBadRequest(response)

    def test_register_partner_limit_reached(self):
        """
        Test that on limit exceeding, the user is created with status
        'waiting' in the PartnerUser table, and a 400 error is thrown
        :return : None
        """

        self.partner.configuration = {'USER_LIMIT': '0'}
        self.partner.save()
        # create focus area with default values
        FocusAreaFactory()

        response = self.client.post(self.registration_url, {
            'name': self.NAME,
            'organization_name': self.ORGANIZATION,
            'country': self.COUNTRY,
            'email': self.EMAIL,
            'username': self.USERNAME,
            'password': self.PASSWORD,
            'terms_of_service': self.TERMS_OF_SERVICE
        })

        self.assertHttpBadRequest(response)
        user = User.objects.filter(username=self.USERNAME).first()
        self.assertIsNotNone(user)
        self.assertEqual(PartnerUser.objects.filter(user=user).first().status, PARTNER_USER_STATUS_WAITING)
