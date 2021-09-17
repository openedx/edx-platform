from django.forms import ModelForm

from .models import ContactUs


class ContactUsForm(ModelForm):
    class Meta:
        model = ContactUs
        fields = ('full_name', 'email', 'organization', 'phone', 'message')

    def __init__(self, *args, **kwargs):
        super(ContactUsForm, self).__init__(*args, **kwargs)
        for key, field in self.fields.items():
            self.fields[key].widget.attrs.update({'class': 'form-control', 'placeholder': field.label})
