"""
Forms for webinars app.
"""
from django import forms
from django.utils.translation import ugettext_lazy as _

from openedx.adg.lms.webinars.models import Webinar

from .constants import UTC_TIMEZONE_HELP_TEXT
from .helpers import validate_email_list


class WebinarForm(forms.ModelForm):
    """
    Webinar Form to create/edit a webinar from admin side
    """

    send_update_emails = forms.BooleanField(
        required=False, label=_(
            'Send update email to registered users and to existing co-hosts, panelists, and presenter'
        )
    )
    invite_all_platform_users = forms.BooleanField(required=False, label=_('Invite all Omnipreneurship Academy users'))

    class Meta:
        model = Webinar
        fields = '__all__'
        help_texts = {
            'start_time': UTC_TIMEZONE_HELP_TEXT,
            'end_time': UTC_TIMEZONE_HELP_TEXT,
        }

    def clean_invites_by_email_address(self):
        """
        Check that the invitees contains 'comma-separated' emails
        and normalizes the data to a list of the email strings.
        """
        invites_by_email_address = self.cleaned_data.get('invites_by_email_address')
        error = validate_email_list(invites_by_email_address)
        if error:
            raise forms.ValidationError(_("Please enter valid email addresses"))
        return invites_by_email_address
