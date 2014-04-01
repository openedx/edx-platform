"""
Utility functions for validating forms
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.hashers import UNUSABLE_PASSWORD
from django.utils.translation import ugettext_lazy as _

class PasswordResetFormNoActive(PasswordResetForm):
    def clean_email(self):
        """
        This is a literal copy from Django 1.4.5's django.contrib.auth.forms.PasswordResetForm
        Except removing the requirement of active users
        Validates that a user exists with the given email address.
        """
        email = self.cleaned_data["email"]
        #The line below contains the only change, removing is_active=True
        self.users_cache = User.objects.filter(email__iexact=email)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        if any((user.password == UNUSABLE_PASSWORD)
               for user in self.users_cache):
            raise forms.ValidationError(self.error_messages['unusable'])
        return email


class SetPasswordFormErrorMessages(SetPasswordForm):
    """
    A form to enter new password.
    The only change from django.contrib.auth.forms.SetResignReasonForm is error_messages.
    """
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput,
        error_messages={'required': _('New password is required.')},
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        widget=forms.PasswordInput,
        error_messages={'required': _('New password confirmation is required.')},
    )
