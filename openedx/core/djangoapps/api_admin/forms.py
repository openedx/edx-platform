"""Forms for API management."""
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from openedx.core.djangoapps.api_admin.models import ApiAccessRequest, Catalog
from openedx.core.djangoapps.api_admin.widgets import TermsOfServiceCheckboxInput


class ApiAccessRequestForm(forms.ModelForm):
    """Form to request API access."""
    terms_of_service = forms.BooleanField(widget=TermsOfServiceCheckboxInput(), label='')

    class Meta(object):
        model = ApiAccessRequest
        fields = ('company_name', 'website', 'company_address', 'reason', 'terms_of_service')
        labels = {
            'company_name': _('Company Name'),
            'company_address': _('Company Address'),
            'reason': _('Describe what your application does.'),
        }
        help_texts = {
            'reason': None,
            'website': _("The URL of your company's website."),
            'company_name': _('The name of your company.'),
            'company_address': _('The contact address of your company.'),
        }
        widgets = {
            'company_address': forms.Textarea()
        }

    def __init__(self, *args, **kwargs):
        # Get rid of the colons at the end of the field labels.
        kwargs.setdefault('label_suffix', '')
        super(ApiAccessRequestForm, self).__init__(*args, **kwargs)


class ViewersWidget(forms.widgets.TextInput):
    """Form widget to display a comma-separated list of usernames."""

    def render(self, name, value, attrs=None):
        return super(ViewersWidget, self).render(name, ', '.join(value), attrs)


class ViewersField(forms.Field):
    """Custom form field for a comma-separated list of usernames."""

    widget = ViewersWidget

    default_error_messages = {
        'invalid': 'Enter a comma-separated list of usernames.',
    }

    def to_python(self, value):
        """Parse out a comma-separated list of usernames."""
        return [username.strip() for username in value.split(',')]

    def validate(self, value):
        super(ViewersField, self).validate(value)
        nonexistent_users = []
        for username in value:
            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                nonexistent_users.append(username)
        if nonexistent_users:
            raise forms.ValidationError(
                _('The following users do not exist: {usernames}.').format(usernames=nonexistent_users)
            )


class CatalogForm(forms.ModelForm):
    """Form to create a catalog."""

    viewers = ViewersField()

    class Meta(object):
        model = Catalog
        fields = ('name', 'query', 'viewers')
        help_texts = {
            'viewers': _('Comma-separated list of usernames which will be able to view this catalog.'),
        }
