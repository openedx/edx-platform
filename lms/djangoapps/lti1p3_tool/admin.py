from __future__ import absolute_import

import json

from django.contrib import admin
from .models import LtiTool, LtiToolKey


class LtiToolKeyAdmin(admin.ModelAdmin):
    """Admin for LTI Tool Key"""
    list_display = ('id', 'name')

    add_fieldsets = (
        (None, {'fields': ('name',)}),
    )

    change_fieldsets = (
        (None, {'fields': ('name', 'private_key_hidden', 'public_key', 'public_key_jwk_json')}),
    )

    readonly_fields = ('private_key_hidden', 'public_key', 'public_key_jwk_json')

    def get_form(self, request, obj=None, **kwargs):
        help_texts = {'public_key_jwk_json': "Tool's generated Public key presented as JWK. "
                                             "Provide this value to Platforms"}
        kwargs.update({'help_texts': help_texts})
        return super(LtiToolKeyAdmin, self).get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        else:
            return self.change_fieldsets

    def private_key_hidden(self, obj):
        return '<hidden>'

    private_key_hidden.short_description = 'Private key'

    def public_key_jwk_json(self, obj):
        return json.dumps(obj.public_jwk)

    public_key_jwk_json.short_description = "Public key in JWK format"


class LtiToolAdmin(admin.ModelAdmin):
    """Admin for LTI Tool"""
    search_fields = ('issuer', 'client_id', 'auth_login_url', 'auth_token_url', 'key_set_url')
    list_display = ('id', 'issuer', 'client_id', 'deployment_ids', 'force_create_lineitem')


admin.site.register(LtiToolKey, LtiToolKeyAdmin)
admin.site.register(LtiTool, LtiToolAdmin)
