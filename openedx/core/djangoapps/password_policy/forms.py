"""
Forms for the password policy app.
"""


import six

from django.contrib import messages
from django.contrib.admin.forms import AdminAuthenticationForm
from django.forms import ValidationError

from openedx.core.djangoapps.password_policy import compliance as password_policy_compliance


class PasswordPolicyAwareAdminAuthForm(AdminAuthenticationForm):
    """
    Custom AdminAuthenticationForm that can enforce password policy rules on login.
    """

    def clean(self):
        """
        Overrides the clean method to allow for the enforcement of password policy requirements.
        """
        cleaned_data = super(PasswordPolicyAwareAdminAuthForm, self).clean()

        if password_policy_compliance.should_enforce_compliance_on_login():
            try:
                password_policy_compliance.enforce_compliance_on_login(self.user_cache, cleaned_data['password'])
            except password_policy_compliance.NonCompliantPasswordWarning as e:
                # Allow login, but warn the user that they will be required to reset their password soon.
                messages.warning(self.request, six.text_type(e))
            except password_policy_compliance.NonCompliantPasswordException as e:
                # Prevent the login attempt.
                raise ValidationError(six.text_type(e))

        return cleaned_data
