from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _


class PartnerResetPasswordForm(forms.Form):
    """
    A form to validate reset password data for partner users. It is currently only used for
    validation, not rendering.
    """

    def clean_email(self):
        email = self.cleaned_data['email']
        """ Check if user associated with email exists"""
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("We don't recognize the email: {}").format(email))
        return email

    email = forms.EmailField(
        error_messages={
            "required": "Valid email is required",
        }
    )

