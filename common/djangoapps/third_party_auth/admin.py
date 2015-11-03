# -*- coding: utf-8 -*-
"""
Admin site configuration for third party authentication
"""
from django import forms

from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin
from .models import (
    OAuth2ProviderConfig,
    SAMLProviderConfig,
    SAMLConfiguration,
    SAMLProviderData,
    LTIProviderConfig,
    ProviderApiPermissions
)
from .tasks import fetch_saml_metadata
from third_party_auth.provider import Registry


class OAuth2ProviderConfigAdmin(KeyedConfigurationModelAdmin):
    """ Django Admin class for OAuth2ProviderConfig """
    def get_list_display(self, request):
        """ Don't show every single field in the admin change list """
        return (
            'name', 'enabled', 'backend_name', 'secondary', 'skip_registration_form',
            'skip_email_verification', 'change_date', 'changed_by', 'edit_link',
        )

admin.site.register(OAuth2ProviderConfig, OAuth2ProviderConfigAdmin)


class SAMLProviderConfigAdmin(KeyedConfigurationModelAdmin):
    """ Django Admin class for SAMLProviderConfig """
    def get_list_display(self, request):
        """ Don't show every single field in the admin change list """
        return (
            'name', 'enabled', 'backend_name', 'entity_id', 'metadata_source',
            'has_data', 'icon_class', 'change_date', 'changed_by', 'edit_link'
        )

    def has_data(self, inst):
        """ Do we have cached metadata for this SAML provider? """
        if not inst.is_active:
            return None  # N/A
        data = SAMLProviderData.current(inst.entity_id)
        return bool(data and data.is_valid())
    has_data.short_description = u'Metadata Ready'
    has_data.boolean = True

    def save_model(self, request, obj, form, change):
        """
        Post save: Queue an asynchronous metadata fetch to update SAMLProviderData.
        We only want to do this for manual edits done using the admin interface.

        Note: This only works if the celery worker and the app worker are using the
        same 'configuration' cache.
        """
        super(SAMLProviderConfigAdmin, self).save_model(request, obj, form, change)
        fetch_saml_metadata.apply_async((), countdown=2)

admin.site.register(SAMLProviderConfig, SAMLProviderConfigAdmin)


class SAMLConfigurationAdmin(ConfigurationModelAdmin):
    """ Django Admin class for SAMLConfiguration """
    def get_list_display(self, request):
        """ Shorten the public/private keys in the change view """
        return (
            'change_date', 'changed_by', 'enabled', 'entity_id',
            'org_info_str', 'key_summary',
        )

    def key_summary(self, inst):
        """ Short summary of the key pairs configured """
        public_key = inst.get_setting('SP_PUBLIC_CERT')
        private_key = inst.get_setting('SP_PRIVATE_KEY')
        if not public_key or not private_key:
            return u'<em>Key pair incomplete/missing</em>'
        pub1, pub2 = public_key[0:10], public_key[-10:]
        priv1, priv2 = private_key[0:10], private_key[-10:]
        return u'Public: {}…{}<br>Private: {}…{}'.format(pub1, pub2, priv1, priv2)
    key_summary.allow_tags = True

admin.site.register(SAMLConfiguration, SAMLConfigurationAdmin)


class SAMLProviderDataAdmin(admin.ModelAdmin):
    """ Django Admin class for SAMLProviderData (Read Only) """
    list_display = ('entity_id', 'is_valid', 'fetched_at', 'expires_at', 'sso_url')
    readonly_fields = ('is_valid', )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.model._meta.get_all_field_names()  # pylint: disable=protected-access
        return self.readonly_fields

admin.site.register(SAMLProviderData, SAMLProviderDataAdmin)


class LTIProviderConfigAdmin(KeyedConfigurationModelAdmin):
    """ Django Admin class for LTIProviderConfig """

    exclude = (
        'icon_class',
        'secondary',
    )

    def get_list_display(self, request):
        """ Don't show every single field in the admin change list """
        return (
            'name',
            'enabled',
            'lti_consumer_key',
            'lti_max_timestamp_age',
            'change_date',
            'changed_by',
            'edit_link',
        )

admin.site.register(LTIProviderConfig, LTIProviderConfigAdmin)


class ApiPermissionsAdminForm(forms.ModelForm):
    """ Django admin form for ApiPermissions model """
    class Meta(object):  # pylint: disable=missing-docstring
        model = ProviderApiPermissions

    provider_id = forms.ChoiceField(choices=[], required=True)

    def __init__(self, *args, **kwargs):
        super(ApiPermissionsAdminForm, self).__init__(*args, **kwargs)
        self.fields['provider_id'].choices = (
            (provider.provider_id, "{} ({})".format(provider.name, provider.provider_id))
            for provider in Registry.enabled()
        )


class ApiPermissionsAdmin(admin.ModelAdmin):
    """ Django Admin class for ApiPermissions """
    list_display = ('client', 'provider_id')
    form = ApiPermissionsAdminForm

admin.site.register(ProviderApiPermissions, ApiPermissionsAdmin)
