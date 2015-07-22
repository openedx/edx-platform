"""
django admin pages for certificates models
"""
from django.contrib import admin
from django import forms
from config_models.admin import ConfigurationModelAdmin
from util.organizations_helpers import get_organizations
from certificates.models import (
    CertificateGenerationConfiguration,
    CertificateHtmlViewConfiguration,
    BadgeImageConfiguration,
    CertificateTemplate,
    CertificateTemplateAsset,
)


class CertificateTemplateForm(forms.ModelForm):
    """
    Django admin form for CertificateTemplate model
    """
    organizations = get_organizations()
    org_choices = [(org["id"], org["name"]) for org in organizations]
    org_choices.insert(0, ('', 'None'))
    organization_id = forms.TypedChoiceField(choices=org_choices, required=False, coerce=int, empty_value=None)

    class Meta(object):
        """ Meta definitions for CertificateTemplateForm  """
        model = CertificateTemplate


class CertificateTemplateAdmin(admin.ModelAdmin):
    """
    Django admin customizations for CertificateTemplate model
    """
    list_display = ('name', 'description', 'organization_id', 'course_key', 'mode', 'is_active')
    form = CertificateTemplateForm


class CertificateTemplateAssetAdmin(admin.ModelAdmin):
    """
    Django admin customizations for CertificateTemplateAsset model
    """
    list_display = ('description', '__unicode__')


admin.site.register(CertificateGenerationConfiguration)
admin.site.register(CertificateHtmlViewConfiguration, ConfigurationModelAdmin)
admin.site.register(BadgeImageConfiguration)
admin.site.register(CertificateTemplate, CertificateTemplateAdmin)
admin.site.register(CertificateTemplateAsset, CertificateTemplateAssetAdmin)
