from django.forms import ModelForm
from django.utils.translation import ugettext as _

from openedx.features.pakx.lms.overrides.utils import validate_text_for_emoji

from .models import ContactUs


class ContactUsForm(ModelForm):
    class Meta:
        model = ContactUs
        fields = ('full_name', 'email', 'organization', 'phone', 'message')
        error_messages = {
            'email': {
                'invalid': _('Invalid email format. Email should be like joey@pakistanx.com'),
            },
        }

    def __init__(self, *args, **kwargs):
        super(ContactUsForm, self).__init__(*args, **kwargs)
        for key, field in self.fields.items():
            if field.required:
                field.label = field.label + '*'
            self.fields[key].widget.attrs.update({'class': 'form-control', 'placeholder': field.label})

    def clean_organization(self):
        value = self.cleaned_data['organization']
        validate_text_for_emoji(value)
        return value
