"""
This module contains forms for the Import model and related functionality.
"""
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.contrib.auth import get_user_model
from openedx.core.djangoapps.content_libraries.api import ContentLibrary

from .models import Import as _Import
from .validators import validate_usage_keys_to_import


User = get_user_model()
admin.autodiscover()


class ImportCreateForm(forms.ModelForm):
    """
    Form for creating an Import instance.
    """
    class Meta:
        model = _Import
        fields = ['source_key', 'target_change', 'user', 'composition_level', 'override']

    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=True,
        label='User',
        widget=ForeignKeyRawIdWidget(_Import._meta.get_field('user').remote_field, admin.site)
    )
    usage_keys_string = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Comma separated list of usage keys to import.',
        }),
        required=True,
        label='Usage Keys to Import',
    )
    library = forms.ModelChoiceField(queryset=ContentLibrary.objects.all(), required=False)

    def clean_usage_keys_string(self):
        """
        Validate the usage keys string.
        """
        usage_keys_string = self.cleaned_data.get('usage_keys_string')
        splitted_keys = usage_keys_string.split(',')
        validate_usage_keys_to_import(splitted_keys)
        return usage_keys_string.split(',')
