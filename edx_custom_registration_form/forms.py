from django.forms import ModelForm
from django.utils.translation import ugettext as _
from .models import PhoneInfo


class PhoneInfoForm(ModelForm):
    """
    This form extends the user registration form to include fields for a Phone Number
    """
    class Meta(object):
        model = PhoneInfo
        fields = ('country_code', 'phone_number')

    def __init__(self, *args, **kwargs):
        super(PhoneInfoForm, self).__init__(*args, **kwargs)
        self.fields['country_code'].error_messages = {
            "required": _('Please select your country code from the list.')
        }
        self.fields['phone_number'].error_messages = {
            "required": _('Please enter your phone number'),
            "invalid": _('This Phone Number seems invalid, please check your input.'),
        }
