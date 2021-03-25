"""
Tests for overridden password reset form.
"""

import json

from django.test import TestCase
from django.test.utils import override_settings

from openedx.adg.lms.user_authn_override.password_reset import get_password_reset_form_override
from openedx.core.djangoapps.user_api.accounts import EMAIL_MAX_LENGTH, EMAIL_MIN_LENGTH
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
class PasswordResetFormTest(TestCase):
    """Tests password reset form."""

    @override_settings(LOGIN_ISSUE_SUPPORT_LINK='')
    def test_password_reset_form(self):
        form_desc = json.loads(get_password_reset_form_override().to_json())

        self.assertEqual(
            form_desc['fields'], [
                {
                    'required': True,
                    'placeholder': 'Email',
                    'restrictions': {'max_length': EMAIL_MAX_LENGTH, 'min_length': EMAIL_MIN_LENGTH},
                    'errorMessages': {},
                    'label': 'Email',
                    'instructions': '',
                    'name': 'email',
                    'supplementalText': '',
                    'defaultValue': '',
                    'type': 'email',
                    'supplementalLink': '',
                    'loginIssueSupportLink': ''
                }
            ]
        )
