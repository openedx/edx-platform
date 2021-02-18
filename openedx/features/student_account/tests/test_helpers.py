from ddt import ddt, data
from django.test import RequestFactory, TestCase
from mock import patch

from lms.djangoapps.onboarding.models import Organization, OrgSector, TotalEmployee
from lms.djangoapps.onboarding.tests.factories import UserFactory
from openedx.features.partners.tests.factories import OrganizationFactory
from openedx.features.student_account.forms import AccountCreationFormCustom
from openedx.features.student_account.helpers import (
    compose_and_send_activation_email_custom,
    save_user_utm_info,
    set_opt_in_and_affiliate_user_organization
)
from openedx.features.user_leads.models import UserLeads
from student.tests.factories import RegistrationFactory


class TestComposeAndSendActivationEmail(TestCase):
    """
    The purpose of this test is to check that the data being passed to the
    compose_and_send_activation_email_custom method stays the same.

    For this, we create a request, user, and registration type objects to
    generate the data just as the helper is supposed to and assert that
    it is the same
    """

    def setUp(self):
        """
        Create a new POST request using the RequestFactory, a user object
        using the UserFactory and a registration object using RegistrationFactory
        for each test case
        """
        self.request = RequestFactory().post('/user_api/v1/account/registration/')
        self.user = UserFactory.create()
        self.registration = RegistrationFactory.create(user=self.user)

    @patch('openedx.features.student_account.helpers.task_send_account_activation_email.delay')
    def test_compose_and_send_email_custom_normal(self, mock_email_task):
        """
        Generate the data using the objects created in setUp, and assert that the
        activation email method is called only once and the data passed to it is
        the same as we expect
        """
        email_data = {
            'activation_link': 'http://edx.org/activate/{}'.format(self.registration.activation_key),
            'user_email': self.user.email,
            'first_name': self.user.first_name,
        }

        compose_and_send_activation_email_custom(self.request, self.registration, self.user)
        mock_email_task.assert_called_once_with(email_data)


class TestSaveUserUTMInfo(TestCase):
    """
    The purpose of this test suite is to ensure that the save_user_utm_info
    helper always works, no matter if the user provides all, partial or no
    utm parameters.
    """

    def setUp(self):
        """
        Create a user object using UserFactory for each test case
        """
        self.user = UserFactory.create()

    def test_save_utm_normal(self):
        """
        Create sample utm parameters data, pass it as POST request parameters
        and assert that the UserLeads object created has all the same values
        as were passed in the request.
        """
        utm_data_to_save = {
            'utm_source': 'testSource1',
            'utm_medium': 'testMedium',
            'utm_campaign': 'testCampaign',
            'utm_content': 'testContent',
            'utm_term': 'testTerm'
        }

        request = RequestFactory().post(
            '/user_api/v1/account/registration/', utm_data_to_save
        )

        save_user_utm_info(request, self.user)
        saved_utm = UserLeads.objects.filter(user=self.user).values(*utm_data_to_save.keys()).first()
        self.assertDictEqual(saved_utm, utm_data_to_save)

    def test_save_utm_empty(self):
        """
        Create a request with no UTM params and assert that the UserLeads
        object created is the database is None
        """
        request = RequestFactory().post(
            '/user_api/v1/account/registration/'
        )

        save_user_utm_info(request, self.user)
        saved_utm = UserLeads.objects.filter(user=self.user).first()
        assert saved_utm is None

    def test_save_utm_no_request(self):
        """
        Ensure that sending None as a request to the save_user_utm_info
        method throws an exception
        """
        request = None
        save_user_utm_info(request, self.user)
        self.assertRaises(Exception, save_user_utm_info)


@ddt
class TestSetOptInAndAffiliateOrganization(TestCase):
    """
    The purpose of this test suite is to check if the set_opt_in_and_affiliate_user_organization
    method is working for both affiliated and unaffiliated users. Also, that the user is affiliated
    with the existing organization or a new organization is created and the user is the first learner.

    This suite also tests that the email preferences model object for the user is created.
    """

    def setUp(self):
        """
        Create a dictionary containing the request data for user registration for
        each test case. This dictionary is modified by inserting new keys depending
        on the test case.

        Also create a user type object using UserFactory, for each new test case.
        """
        self.request_data = {
            'email': 'testUser@example.com',
            'username': 'testUser',
            'password': 'Edx123',
            'first_name': 'Test',
            'last_name': 'User',
            'honor_code': 'true',
            'opt_in': 'yes',
        }
        self.user = UserFactory.create()

    @patch('openedx.features.student_account.helpers.Organization.objects.get_or_create')
    @patch('openedx.features.student_account.helpers.EmailPreference.objects.create')
    @patch('openedx.features.student_account.helpers.UserExtendedProfile.objects.create')
    def test_unaffiliated_user(self, mock_user_extended_profile_create_method,
                               mock_email_preferences_create_method, mock_org_get_or_create_method):
        """
        Test that when no organization related data is present in the request, the
        form cleans the data without raising any validation errors, passes the
        data to set_opt_in_and_affiliate_user_organization method, does not
        fetch an existing organization or create a new organization,
        and then saves the UserExtendedProfile and EmailPreferences
        """
        request = RequestFactory().post('/user_api/v1/account/registration/',
                                        self.request_data)
        params = dict(request.POST.copy().items())
        params['name'] = '{f_name} {l_name}'.format(f_name=params.get('first_name'), l_name=params.get('last_name'))

        form = AccountCreationFormCustom(data=params,
                                         extended_profile_fields=None,
                                         do_third_party_auth=False)
        form.is_valid()
        set_opt_in_and_affiliate_user_organization(self.user, form)

        mock_org_get_or_create_method.assert_not_called()
        mock_user_extended_profile_create_method.assert_called_once_with(user=self.user, **{})
        mock_email_preferences_create_method.assert_called_once_with(user=self.user, opt_in=form.cleaned_data.get('opt_in'))

    @patch('openedx.features.student_account.helpers.EmailPreference.objects.create')
    @patch('openedx.features.student_account.helpers.UserExtendedProfile.objects.create')
    def test_user_with_new_organization(self, mock_user_extended_profile_create_method,
                                        mock_email_preferences_create_method):
        """
        Test that when the user gives a new organization fields in the request,
        the form does not raise any validation error.

        A new organization is created, and the user is made first_learner for that
        organization in the UserExtendedProfile and the EmailPreferences are
        also set for that user
        """
        self.request_data['organization_name'] = 'new_organization'
        self.request_data['organization_size'] = '6-10'
        self.request_data['organization_type'] = 'IWRNS'

        request = RequestFactory().post('/user_api/v1/account/registration/', self.request_data)
        params = dict(request.POST.copy().items())
        params['name'] = '{f_name} {l_name}'.format(f_name=params.get('first_name'), l_name=params.get('last_name'))
        OrgSector.objects.create(order=1, code='IWRNS')
        TotalEmployee.objects.create(order=1, code='6-10')

        form = AccountCreationFormCustom(data=params,
                                         extended_profile_fields=None,
                                         do_third_party_auth=False)
        form.is_valid()

        set_opt_in_and_affiliate_user_organization(self.user, form)
        created_organization = Organization.objects.filter(label=form.cleaned_data.get('organization_name')).first()

        user_extended_profile_data = {
            'is_first_learner': True,
            'organization_id': created_organization.id
        }

        self.assertEqual(created_organization.label, self.request_data['organization_name'])
        self.assertEqual(created_organization.total_employees, self.request_data['organization_size'])
        self.assertEqual(created_organization.org_type, self.request_data['organization_type'])
        mock_user_extended_profile_create_method.assert_called_once_with(user=self.user, **user_extended_profile_data)
        mock_email_preferences_create_method.assert_called_once_with(user=self.user,
                                                                     opt_in=form.cleaned_data.get('opt_in'))

    @data(True, False)
    @patch('openedx.features.student_account.helpers.EmailPreference.objects.create')
    @patch('openedx.features.student_account.helpers.UserExtendedProfile.objects.create')
    def test_user_with_existing_organization(self, is_org_orphan, mock_user_extended_profile_create_method,
                                             mock_email_preferences_create_method):
        """
        Test that when a user gives the name of an already existing organization,
        they are affiliated with that organization. The form does not raise any validation
        errors, the EmailPreferences are also set for that user.
        """
        organization_data = {
            'label': 'existing_organization',
            'total_employees': '6-10',
            'org_type': 'IWRNS'
        }

        existing_organization = OrganizationFactory(**organization_data)
        user_extended_profile_data = {
            'is_first_learner': is_org_orphan,
            'organization_id': existing_organization.id,
        }

        if not is_org_orphan:
            # Add one user to organization, so that it does not remain orphan
            UserFactory(extended_profile__organization=existing_organization)

        form = AccountCreationFormCustom(
            data={
                'organization_name': existing_organization.label,
                'organization_type': existing_organization.org_type,
                'organization_size': existing_organization.total_employees,
                'is_org_selected': True
            },
            extended_profile_fields=None,
            do_third_party_auth=False
        )

        form.is_valid()

        set_opt_in_and_affiliate_user_organization(self.user, form)

        self.assertEqual(existing_organization.label, organization_data['label'])
        self.assertEqual(existing_organization.total_employees, organization_data['total_employees'])
        self.assertEqual(existing_organization.org_type, organization_data['org_type'])
        mock_user_extended_profile_create_method.assert_called_once_with(user=self.user, **user_extended_profile_data)
        mock_email_preferences_create_method.assert_called_once_with(
            user=self.user,
            opt_in=form.cleaned_data.get('opt_in')
        )
