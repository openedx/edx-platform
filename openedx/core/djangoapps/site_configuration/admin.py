"""
Django admin page for Site Configuration models
"""
from dal import autocomplete
import json

from django import forms
from django.urls import path
from django.contrib import admin

from .constants import FEATURE_FLAGS
from .models import SiteConfiguration, SiteConfigurationHistory

class FeatureFlagAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        return list(FEATURE_FLAGS.keys())

    def get_result_label(self, item):
        return item

    def get_result_value(self, item):
        return item


class SiteConfigurationForm(forms.ModelForm):
    feature_flags = forms.Field(
        required=False,
        widget=autocomplete.Select2Multiple(
            url='admin:feature-flag-autocomplete',
            attrs={
                'multiple': 'multiple',
                'data-tags': 'true',
                'data-placeholder': 'Select features'
            }
        ),
        label="Enabled Features",
    )

    class Meta:
        model = SiteConfiguration
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        current_values = self.instance.site_values or {}
        selected_labels = []
        for label, mapping in FEATURE_FLAGS.items():
            if all(current_values.get(k) == v for k, v in mapping.items()):
                selected_labels.append(label)

        self.fields['feature_flags'].initial = selected_labels
        self.fields['feature_flags'].widget.choices = [(v, v) for v in selected_labels]


    def clean(self):
        cleaned = super().clean()
        current_site_values = json.loads(self.data.get('site_values', {}))
        selected_flags = self.data.getlist('feature_flags')
        if not isinstance(selected_flags, list):
            selected_flags = [selected_flags] if selected_flags else []

        flag_keys = {key for group in FEATURE_FLAGS.values() for key in group}

        site_values = {}
        for label in selected_flags:
            site_values.update(FEATURE_FLAGS.get(label, {}))

        for key, value in current_site_values.items():
            if key not in flag_keys:
                site_values[key] = value

        cleaned['feature_flags'] = selected_flags
        cleaned['site_values'] = site_values

        return cleaned

class SiteConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for the SiteConfiguration object.
    """
    form = SiteConfigurationForm
    list_display = ('site', 'enabled', 'site_values')
    search_fields = ('site__domain', 'site_values')

    class Meta:
        """
        Meta class for SiteConfiguration admin model
        """
        model = SiteConfiguration

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'feature-flag-autocomplete/',
                FeatureFlagAutocomplete.as_view(),
                name='feature-flag-autocomplete'
            ),
        ]
        return custom_urls + urls

admin.site.register(SiteConfiguration, SiteConfigurationAdmin)


class SiteConfigurationHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for the SiteConfigurationHistory object.
    """
    list_display = ('site', 'enabled', 'created', 'modified')
    search_fields = ('site__domain', 'site_values', 'created', 'modified')

    ordering = ['-created']

    class Meta:
        """
        Meta class for SiteConfigurationHistory admin model
        """
        model = SiteConfigurationHistory

    def has_add_permission(self, request):
        """Don't allow adds"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Don't allow deletes"""
        return False


admin.site.register(SiteConfigurationHistory, SiteConfigurationHistoryAdmin)
