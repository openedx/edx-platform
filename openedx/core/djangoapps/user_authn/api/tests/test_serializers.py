"""Tests for serializers for the MFE Context"""

from django.test import TestCase

from openedx.core.djangoapps.user_authn.serializers import MFEContextSerializer


class TestMFEContextSerializer(TestCase):
    """
    High-level unit tests for MFEContextSerializer
    """

    @staticmethod
    def get_mock_mfe_context_data():
        """
        Helper function to generate mock data for the MFE Context API view.
        """

        mock_context_data = {
            'context_data': {
                'currentProvider': 'edX',
                'platformName': 'edX',
                'providers': [
                    {
                        'id': 'oa2-facebook',
                        'name': 'Facebook',
                        'iconClass': 'fa-facebook',
                        'iconImage': None,
                        'skipHintedLogin': False,
                        'skipRegistrationForm': False,
                        'loginUrl': 'https://facebook.com/login',
                        'registerUrl': 'https://facebook.com/register'
                    },
                    {
                        'id': 'oa2-google-oauth2',
                        'name': 'Google',
                        'iconClass': 'fa-google-plus',
                        'iconImage': None,
                        'skipHintedLogin': False,
                        'skipRegistrationForm': False,
                        'loginUrl': 'https://google.com/login',
                        'registerUrl': 'https://google.com/register'
                    }
                ],
                'secondaryProviders': [],
                'finishAuthUrl': 'https://edx.com/auth/finish',
                'errorMessage': None,
                'registerFormSubmitButtonText': 'Create Account',
                'autoSubmitRegForm': False,
                'syncLearnerProfileData': False,
                'countryCode': '',
                'pipeline_user_details': {
                    'username': 'test123',
                    'email': 'test123@edx.com',
                    'fullname': 'Test Test',
                    'first_name': 'Test',
                    'last_name': 'Test'
                }
            },
            'registration_fields': {},
            'optional_fields': {
                'extended_profile': []
            }
        }

        return mock_context_data

    @staticmethod
    def get_expected_data():
        """
        Helper function to generate expected data for the MFE Context API view serializer.
        """

        expected_data = {
            'contextData': {
                'currentProvider': 'edX',
                'platformName': 'edX',
                'providers': [
                    {
                        'id': 'oa2-facebook',
                        'name': 'Facebook',
                        'iconClass': 'fa-facebook',
                        'iconImage': None,
                        'skipHintedLogin': False,
                        'skipRegistrationForm': False,
                        'loginUrl': 'https://facebook.com/login',
                        'registerUrl': 'https://facebook.com/register'
                    },
                    {
                        'id': 'oa2-google-oauth2',
                        'name': 'Google',
                        'iconClass': 'fa-google-plus',
                        'iconImage': None,
                        'skipHintedLogin': False,
                        'skipRegistrationForm': False,
                        'loginUrl': 'https://google.com/login',
                        'registerUrl': 'https://google.com/register'
                    }
                ],
                'secondaryProviders': [],
                'finishAuthUrl': 'https://edx.com/auth/finish',
                'errorMessage': None,
                'registerFormSubmitButtonText': 'Create Account',
                'autoSubmitRegForm': False,
                'syncLearnerProfileData': False,
                'countryCode': '',
                'pipelineUserDetails': {
                    'username': 'test123',
                    'email': 'test123@edx.com',
                    'name': 'Test Test',
                    'firstName': 'Test',
                    'lastName': 'Test'
                }
            },
            'registrationFields': {},
            'optionalFields': {
                'extended_profile': []
            }
        }

        return expected_data

    def test_mfe_context_serializer(self):
        """
        Test MFEContextSerializer with mock data that serializes data correctly
        """

        mfe_context_data = self.get_mock_mfe_context_data()
        expected_data = self.get_expected_data()
        output_data = MFEContextSerializer(
            mfe_context_data
        ).data

        self.assertDictEqual(
            output_data,
            expected_data
        )
