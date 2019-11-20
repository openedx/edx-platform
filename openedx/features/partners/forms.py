from django import forms
from django.contrib.auth.models import User


class PartnerResetPasswordForm(forms.Form):
    """
    A form to validate reset password data for partner users. It is currently only used for
    validation, not rendering.
    """

    _EMAIL_INVALID_MSG = "A properly formatted e-mail is required"

    def __init__(self, data=None):
        super(PartnerResetPasswordForm, self).__init__(data)

    def validate_user_using_email(email):
        """ Check if user associated with email exists"""
        user = User.objects.filter(email=email).first()
        if user is None:
            raise forms.ValidationError("We don't recognize the email: %s" % email)

    email = forms.EmailField(
        validators=[validate_user_using_email]
    )

