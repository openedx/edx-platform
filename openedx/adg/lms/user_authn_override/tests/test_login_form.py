"""
Tests for login form.
"""

import json
from unittest import mock

from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from common.djangoapps.util.password_policy_validators import DEFAULT_MAX_PASSWORD_LENGTH
from openedx.adg.lms.user_authn_override.login_form import get_login_session_form_override
from openedx.core.djangoapps.user_api.accounts import EMAIL_MAX_LENGTH, EMAIL_MIN_LENGTH
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
class LoginSessionFormTest(TestCase):
    """Tests for the login form of the user API."""

    @override_settings(LOGIN_ISSUE_SUPPORT_LINK='')
    @mock.patch('openedx.core.djangoapps.user_authn.views.login_form.is_testing_environment')
    @mock.patch('openedx.adg.lms.user_authn_override.login_form._apply_third_party_auth_overrides')
    def test_login_form(self, third_party_auth, is_test_env):
        third_party_auth.return_value = None
        is_test_env.return_value = False

        # Retrieve the login form
        request = RequestFactory().get('/login')
        form_desc = json.loads(get_login_session_form_override(request).to_json())

        self.assertEqual(
            form_desc['fields'], [
                {
                    'placeholder': 'Email',
                    'errorMessages': {},
                    'type': 'email',
                    'restrictions': {'max_length': EMAIL_MAX_LENGTH, 'min_length': EMAIL_MIN_LENGTH},
                    'label': 'Email',
                    'instructions': '',
                    'name': 'email',
                    'defaultValue': '',
                    'supplementalText': '',
                    'supplementalLink': '',
                    'required': True,
                    'loginIssueSupportLink': ''
                },
                {
                    'placeholder': 'Password',
                    'errorMessages': {},
                    'type': 'password',
                    'restrictions': {'max_length': DEFAULT_MAX_PASSWORD_LENGTH},
                    'label': 'Password',
                    'instructions': '',
                    'name': 'password',
                    'defaultValue': '',
                    'supplementalText': '',
                    'supplementalLink': '',
                    'required': True,
                    'loginIssueSupportLink': ''
                }
            ]
        )
