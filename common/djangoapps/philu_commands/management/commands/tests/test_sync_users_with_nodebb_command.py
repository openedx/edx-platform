from __future__ import unicode_literals

from django.core.management import call_command
from django.db.models.signals import post_save
from django.test import TestCase
from factory.django import mute_signals
from mock import call, patch
from pynodebb.settings import settings as nodebb_settings

from lms.djangoapps.onboarding.helpers import COUNTRIES
from lms.djangoapps.onboarding.models import UserExtendedProfile
from lms.djangoapps.onboarding.tests.factories import UserFactory

HTTP_SUCCESS = 200
HTTP_NOT_FOUND = 404
POST_METHOD = 'POST'
GET_METHOD = 'GET'


class NodeBBSync(TestCase):
    """
        Tests for `sync_users_with_nodebb` command.
    """
    nodebb_data = {
        'website': '',
        'last_name': 'Test',
        'uid': 2,
        'first_name': 'Robot1',
        'country_of_residence': '',
        'email': 'test@example.com',
        'username': 'test',
        'city_of_residence': '',
        '_key': 'user:10',
        'country_of_employment': '',
        'fullname': 'Robot1 Test',
        'userslug': 'test',
        'edx_user_id': 2,
        'language': 'None'
    }

    nodebb_api_urls = {
        'get_users_data': '/api/v2/users/all',
        'user_creation': '/api/v2/users/create',
        'user_activation': '/api/v2/users/activate',
        'user_update': '/api/v2/users/update',
        'user_onboarding_status_update': '/api/v2/users/update-visibility-status?username={}'
    }

    @mute_signals(post_save)
    def setUp(self):
        super(NodeBBSync, self).setUp()
        self.user = UserFactory(username="test", email="test@example.com", password="123")
        self.user_edx_data = self._generate_edx_user_data()
        patcher = patch('pynodebb.http_client.HttpClient._request')
        self.mocked_pynodebb_request_func = patcher.start()
        self.addCleanup(patcher.stop)

    def test_sync_users_with_nodebb_command_for_user_creation(self):
        """
        This test case is responsible for testing the user creation and activation part of command.
        """
        self.mocked_pynodebb_request_func.return_value = [HTTP_SUCCESS, []]
        call_command('sync_users_with_nodebb')
        self.mocked_pynodebb_request_func.assert_has_calls([call(POST_METHOD, self.nodebb_api_urls['get_users_data']),
                                                            call(POST_METHOD, self.nodebb_api_urls['user_creation'],
                                                                 **self.user_edx_data),
                                                            call(POST_METHOD, self.nodebb_api_urls['user_activation'],
                                                                 username=self.user.username,
                                                                 active=self.user.is_active,
                                                                 _uid=nodebb_settings['admin_uid']),
                                                            call(GET_METHOD,
                                                                 self.nodebb_api_urls['user_onboarding_status_update'].
                                                                 format(self.user.username)),
                                                            call(POST_METHOD, self.nodebb_api_urls['user_activation'],
                                                                 username=self.user.username,
                                                                 active=self.user.is_active,
                                                                 _uid=nodebb_settings['admin_uid'])
                                                            ])
        self.assertEqual(self.mocked_pynodebb_request_func.call_count, 5)

    @patch('lms.djangoapps.onboarding.models.UserExtendedProfile.unattended_surveys', return_value=[])
    def test_sync_users_with_nodebb_command_without_attended_survey(self, mocked_func_of_model):
        """
        This test case is responsible for testing and the user creation and updating the onboarding survey status
        on nodebb if it doesn't have attended any onboarding surveys.
        """
        self.mocked_pynodebb_request_func.return_value = [HTTP_SUCCESS, []]
        call_command('sync_users_with_nodebb')
        self.mocked_pynodebb_request_func.assert_has_calls([call(POST_METHOD, self.nodebb_api_urls['get_users_data']),
                                                            call(POST_METHOD, self.nodebb_api_urls['user_creation'],
                                                                 **self.user_edx_data),
                                                            call(POST_METHOD, self.nodebb_api_urls['user_activation'],
                                                                 username=self.user.username,
                                                                 active=self.user.is_active,
                                                                 _uid=nodebb_settings['admin_uid']),
                                                            call(GET_METHOD,
                                                                 self.nodebb_api_urls[
                                                                     'user_onboarding_status_update'].format(
                                                                     self.user.username)),
                                                            call(POST_METHOD, self.nodebb_api_urls['user_activation'],
                                                                 username=self.user.username,
                                                                 active=self.user.is_active,
                                                                 _uid=nodebb_settings['admin_uid']),
                                                            call(GET_METHOD,
                                                                 self.nodebb_api_urls[
                                                                     'user_onboarding_status_update'].format(
                                                                     self.user.username)),
                                                            ])
        self.assertEqual(self.mocked_pynodebb_request_func.call_count, 6)

    def test_sync_users_with_nodebb_command_for_bad_request(self):
        """
        This test case is responsible for testing the scenario when nodebb returns bad_request. In that case command
        Log the Issue and Terminate and returns nothing.
        """
        self.mocked_pynodebb_request_func.return_value = [HTTP_NOT_FOUND, []]
        call_command('sync_users_with_nodebb')
        self.mocked_pynodebb_request_func.assert_has_calls([call(POST_METHOD, self.nodebb_api_urls['get_users_data'])])
        self.assertEqual(self.mocked_pynodebb_request_func.call_count, 1)

    def test_sync_users_with_nodebb_command_for_user_update(self):
        """
        This test case is responsible for testing the user update part of command. This scenario is generated when a
        user is already generated on nodebb and later user settings(name, date_birth, etc) are updated on edX.
        """
        self.mocked_pynodebb_request_func.return_value = [HTTP_SUCCESS, [self.nodebb_data]]
        call_command('sync_users_with_nodebb')
        self.mocked_pynodebb_request_func.assert_has_calls([call(POST_METHOD, self.nodebb_api_urls['get_users_data']),
                                                            call(POST_METHOD, self.nodebb_api_urls['user_update'],
                                                                 **self.user_edx_data)
                                                            ])
        self.assertEqual(self.mocked_pynodebb_request_func.call_count, 2)

    def _generate_edx_user_data(self):
        """
        This function will generate data we send to nodebb for users.
        """
        extended_profile = UserExtendedProfile.objects.all()[0]
        user = extended_profile.user
        profile = user.profile

        edx_user_data = {
            'edx_user_id': unicode(user.id),
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'country_of_employment': extended_profile.country_of_employment,
            'city_of_employment': extended_profile.city_of_employment,
            'country_of_residence': COUNTRIES.get(profile.country.code),
            'city_of_residence': profile.city,
            'birthday': profile.year_of_birth,
            'language': profile.language,
            'interests': extended_profile.get_user_selected_interests(),
            'self_prioritize_areas': extended_profile.get_user_selected_functions()
        }

        return edx_user_data
