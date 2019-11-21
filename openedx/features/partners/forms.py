from django.utils.translation import ugettext as _

from student.forms import PasswordResetFormNoActive


class PartnerResetPasswordForm(PasswordResetFormNoActive):
    """
    A form to validate reset password data for partner users. This is currently only
    being used to override an error message as per the requirements.
    """
    def clean_email(self):
        self.error_messages['unknown'] = _("We don't recognize the email: {}").format(self.cleaned_data["email"])
        return super(PartnerResetPasswordForm, self).clean_email()

