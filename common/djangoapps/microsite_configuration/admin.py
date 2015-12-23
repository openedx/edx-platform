"""
Django admin page for microsite models
"""
from django.contrib import admin
from django import forms

from .models import (
    Microsite,
    MicrositeHistory,
    MicrositeOrgMapping,
    MicrositeTemplate
)
from util.organizations_helpers import get_organizations


class MicrositeAdmin(admin.ModelAdmin):
    """ Admin interface for the Microsite object. """
    list_display = ('key', 'subdomain')
    search_fields = ('key', 'subdomain', 'values')

    class Meta(object):  # pylint: disable=missing-docstring
        model = Microsite


class MicrositeHistoryAdmin(admin.ModelAdmin):
    """ Admin interface for the Microsite object. """
    list_display = ('key', 'subdomain', 'created')
    search_fields = ('key', 'subdomain', 'values')

    ordering = ['-created']

    class Meta(object):  # pylint: disable=missing-docstring
        model = MicrositeHistory

    def has_add_permission(self, request):
        """Don't allow adds"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Don't allow deletes"""
        return False


class MicrositeOrgMappingForm(forms.ModelForm):
    """
    Django admin form for CertificateTemplate model
    """
    def __init__(self, *args, **kwargs):
        super(MicrositeOrgMappingForm, self).__init__(*args, **kwargs)
        organizations = get_organizations()
        org_choices = [(org["short_name"], org["name"]) for org in organizations]
        org_choices.insert(0, ('', 'None'))
        self.fields['org'] = forms.TypedChoiceField(
            choices=org_choices, required=False, empty_value=None
        )

    class Meta(object):
        model = MicrositeOrgMapping
        fields = '__all__'


class MicrositeOrgMappingAdmin(admin.ModelAdmin):
    """ Admin interface for the Microsite object. """
    list_display = ('org', 'microsite')
    search_fields = ('org', 'microsite')
    form = MicrositeOrgMappingForm

    class Meta(object):  # pylint: disable=missing-docstring
        model = MicrositeOrgMapping


class MicrositeTemplateAdmin(admin.ModelAdmin):
    """ Admin interface for the Microsite object. """
    list_display = ('microsite', 'template_uri')
    search_fields = ('microsite', 'template_uri')

    class Meta(object):  # pylint: disable=missing-docstring
        model = MicrositeTemplate

admin.site.register(Microsite, MicrositeAdmin)
admin.site.register(MicrositeHistory, MicrositeHistoryAdmin)
admin.site.register(MicrositeOrgMapping, MicrositeOrgMappingAdmin)
admin.site.register(MicrositeTemplate, MicrositeTemplateAdmin)
